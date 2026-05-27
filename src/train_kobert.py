from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch import nn
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"
OUTPUT_DIR = REPORT_DIR / "outputs"
FIGURE_DIR = REPORT_DIR / "figures"
LOG_DIR = ROOT / "logs"
MODEL_DIR = ROOT / "models"

SEED = 42
LABELS = {
    0: "인권/성평등",
    1: "문화/예술/체육/언론",
    2: "육아/교육",
}


@dataclass(frozen=True)
class TransformerConfig:
    # DistilKoBERT was the first choice, but Transformers 5.9 failed to
    # instantiate its tokenizer in this environment. KLUE RoBERTa-small is a
    # lightweight Hugging Face Korean Transformer and is used as the compatible
    # Korean BERT-family experiment for this local run.
    model_name: str = "klue/roberta-small"
    seed: int = SEED
    max_length: int = 160
    batch_size: int = 32
    epochs: int = 3
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    max_train_samples: int = 0
    max_valid_samples: int = 0
    max_test_samples: int = 0
    gradient_accumulation_steps: int = 1


class TextDataset(Dataset):
    def __init__(
        self,
        encodings: dict[str, torch.Tensor],
        labels: np.ndarray,
        indices: np.ndarray,
    ) -> None:
        self.encodings = encodings
        self.labels = torch.tensor(labels, dtype=torch.long)
        self.indices = torch.tensor(indices, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = {key: value[idx] for key, value in self.encodings.items()}
        item["labels"] = self.labels[idx]
        item["index"] = self.indices[idx]
        return item


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(False)


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_split_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_clean_path = PROCESSED_DIR / "train_clean.csv"
    split_path = PROCESSED_DIR / "split_indices.csv"
    if not train_clean_path.exists() or not split_path.exists():
        raise FileNotFoundError(
            "Missing processed data or split indices. Run preprocess.py and train_baseline.py first."
        )
    df = pd.read_csv(train_clean_path)
    splits = pd.read_csv(split_path)
    merged = df.merge(splits, on="index", how="inner")
    train_df = merged[merged["split"] == "train"].sort_values("index").reset_index(drop=True)
    valid_df = merged[merged["split"] == "valid"].sort_values("index").reset_index(drop=True)
    test_df = merged[merged["split"] == "test"].sort_values("index").reset_index(drop=True)
    return train_df, valid_df, test_df


def limit_samples(df: pd.DataFrame, max_samples: int, seed: int) -> pd.DataFrame:
    if max_samples <= 0 or len(df) <= max_samples:
        return df.reset_index(drop=True)
    per_class = max_samples // len(LABELS)
    sampled = []
    for label_id in LABELS:
        class_df = df[df["category"] == label_id]
        sampled.append(
            class_df.sample(
                n=min(per_class, len(class_df)),
                random_state=seed,
            )
        )
    result = pd.concat(sampled).sort_values("index").reset_index(drop=True)
    return result


def tokenize_frame(
    tokenizer: AutoTokenizer,
    df: pd.DataFrame,
    config: TransformerConfig,
) -> TextDataset:
    encodings = tokenizer(
        df["clean_text"].fillna("").astype(str).tolist(),
        max_length=config.max_length,
        truncation=True,
        padding="max_length",
        return_tensors="pt",
    )
    return TextDataset(
        encodings=encodings,
        labels=df["category"].to_numpy(),
        indices=df["index"].to_numpy(),
    )


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, float]:
    model.eval()
    criterion = nn.CrossEntropyLoss()
    labels_all: list[np.ndarray] = []
    preds_all: list[np.ndarray] = []
    total_loss = 0.0
    with torch.no_grad():
        for batch in loader:
            labels = batch["labels"].to(device)
            inputs = {
                key: value.to(device)
                for key, value in batch.items()
                if key in {"input_ids", "attention_mask", "token_type_ids"}
            }
            outputs = model(**inputs)
            loss = criterion(outputs.logits, labels)
            total_loss += float(loss.item()) * len(labels)
            preds = torch.argmax(outputs.logits, dim=1)
            labels_all.append(labels.cpu().numpy())
            preds_all.append(preds.cpu().numpy())
    y_true = np.concatenate(labels_all)
    y_pred = np.concatenate(preds_all)
    return y_true, y_pred, total_loss / len(y_true)


def metrics_row(
    model_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    elapsed: float,
    config: dict[str, object],
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    report = classification_report(
        y_true,
        y_pred,
        labels=list(LABELS.keys()),
        target_names=[LABELS[i] for i in LABELS],
        output_dict=True,
        zero_division=0,
    )
    row = {
        "model": model_name,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6),
        "macro_precision": round(float(report["macro avg"]["precision"]), 6),
        "macro_recall": round(float(report["macro avg"]["recall"]), 6),
        "macro_f1": round(float(report["macro avg"]["f1-score"]), 6),
        "weighted_precision": round(float(report["weighted avg"]["precision"]), 6),
        "weighted_recall": round(float(report["weighted avg"]["recall"]), 6),
        "weighted_f1": round(float(report["weighted avg"]["f1-score"]), 6),
        "elapsed_seconds": round(elapsed, 2),
        "config": json.dumps(config, ensure_ascii=False),
    }
    class_rows = []
    for label_id, label_name in LABELS.items():
        values = report[label_name]
        class_rows.append(
            {
                "model": model_name,
                "label_id": label_id,
                "label": label_name,
                "precision": round(float(values["precision"]), 6),
                "recall": round(float(values["recall"]), 6),
                "f1": round(float(values["f1-score"]), 6),
                "support": int(values["support"]),
            }
        )
    matrix = confusion_matrix(y_true, y_pred, labels=list(LABELS.keys()))
    matrix_df = pd.DataFrame(
        matrix,
        index=[f"true_{i}_{LABELS[i]}" for i in LABELS],
        columns=[f"pred_{i}_{LABELS[i]}" for i in LABELS],
    )
    return row, pd.DataFrame(class_rows), matrix_df


def write_matrix_svg(path: Path, title: str, matrix_df: pd.DataFrame) -> None:
    matrix = matrix_df.to_numpy()
    width, height = 620, 560
    cell = 120
    x0, y0 = 210, 90
    max_value = max(1, int(matrix.max()))
    cells: list[str] = []
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = int(matrix[i, j])
            intensity = 245 - int(150 * value / max_value)
            fill = f"rgb({intensity},{intensity},255)"
            x = x0 + j * cell
            y = y0 + i * cell
            cells.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" stroke="#334155" />')
            cells.append(f'<text x="{x + cell / 2}" y="{y + cell / 2 + 5}" text-anchor="middle" font-size="22">{value}</text>')
    row_labels = [
        f'<text x="{x0 - 12}" y="{y0 + i * cell + cell / 2 + 5}" text-anchor="end" font-size="14">true {i}</text>'
        for i in range(matrix.shape[0])
    ]
    col_labels = [
        f'<text x="{x0 + j * cell + cell / 2}" y="{y0 - 14}" text-anchor="middle" font-size="14">pred {j}</text>'
        for j in range(matrix.shape[1])
    ]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white" />
<text x="{width / 2}" y="35" text-anchor="middle" font-size="22" font-weight="700">{title}</text>
{''.join(col_labels)}
{''.join(row_labels)}
{''.join(cells)}
<text x="{width / 2}" y="{height - 35}" text-anchor="middle" font-size="13">0=인권/성평등, 1=문화/예술/체육/언론, 2=육아/교육</text>
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def write_report(
    config: TransformerConfig,
    metrics: pd.DataFrame,
    baseline: pd.DataFrame,
    train_size: int,
    valid_size: int,
    test_size: int,
) -> None:
    row = metrics.iloc[0]
    baseline_best = baseline.sort_values("macro_f1", ascending=False).iloc[0]
    improvement = float(row["macro_f1"]) - float(baseline_best["macro_f1"])
    device = json.loads(row["config"])["device"]
    sample_note = (
        "전체 baseline split을 사용했다."
        if config.max_train_samples <= 0 and config.max_valid_samples <= 0
        else "CPU 환경 제약 때문에 train/validation은 stratified subset으로 줄였고, test는 동일 split 전체를 평가했다."
    )
    report = f"""# KoBERT 호환 한국어 Transformer 파인튜닝 결과

## 1. 모델 선택

- 1차 후보: `monologg/distilkobert`
- 실제 사용 모델: `{config.model_name}`
- 선택 사유: `monologg/distilkobert`는 현재 Transformers 5.9 환경에서 tokenizer 로딩이 실패했다. `klue/roberta-small`은 Hugging Face에서 바로 로딩 가능한 경량 한국어 Transformer이며, 로컬 CUDA 환경에서 전체 split 재학습이 가능한 KoBERT 호환 실험군으로 사용했다.

## 2. 학습 설정

- Seed: `{config.seed}`
- Max length: `{config.max_length}`
- Batch size: `{config.batch_size}`
- Epochs: `{config.epochs}`
- Learning rate: `{config.learning_rate}`
- Weight decay: `{config.weight_decay}`
- Device: `{device}`
- Train samples: `{train_size:,}` from baseline train split
- Validation samples: `{valid_size:,}` from baseline validation split
- Test samples: `{test_size:,}` from baseline test split
- Gradient accumulation: `{config.gradient_accumulation_steps}`

{sample_note}

## 3. 하이퍼파라미터 선택 근거

- `max_length=160`: 국민청원 본문이 길기 때문에 1차 CPU 실험의 96보다 길게 잡아 더 많은 문맥을 반영한다.
- `batch_size=32`: RTX 3080 12GB GPU에서 `klue/roberta-small`을 안정적으로 학습할 수 있는 크기로 설정했다.
- `epochs=3`: 1차 실험의 1 epoch보다 길게 학습하여 validation F1 기준의 모델 선택이 가능하도록 했다.
- `learning_rate=2e-5`: BERT 계열 fine-tuning에서 널리 쓰이는 보수적 학습률로, 사전학습 가중치를 급격히 훼손하지 않기 위해 선택했다.
- `weight_decay=0.01`: fine-tuning 중 과적합을 완화하기 위해 적용했다.
- `gradient_accumulation_steps=1`: GPU 메모리 부족이 발생하지 않아 추가 누적은 사용하지 않았다.
- `max_train_samples=0`, `max_valid_samples=0`: subset 제한 없이 baseline과 동일한 전체 train/validation split을 사용한다.

## 4. 테스트 성능

| model | accuracy | macro precision | macro recall | macro F1 | weighted F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| {row["model"]} | {float(row["accuracy"]):.4f} | {float(row["macro_precision"]):.4f} | {float(row["macro_recall"]):.4f} | {float(row["macro_f1"]):.4f} | {float(row["weighted_f1"]):.4f} |

## 5. 베이스라인 대비

- 가장 높은 베이스라인 macro F1: `{baseline_best["model"]}` = `{float(baseline_best["macro_f1"]):.4f}`
- Transformer macro F1: `{float(row["macro_f1"]):.4f}`
- 차이: `{improvement:+.4f}`

이번 결과는 GPU 환경에서 전체 train split, 더 긴 epoch, 더 큰 max length로 재학습한 결과다. 베이스라인 대비 성능 개선 여부를 최종 비교 근거로 사용한다.

## 6. 산출물

- `src/train_kobert.py`
- `reports/outputs/kobert_metrics.csv`
- `reports/outputs/kobert_classification_report.csv`
- `reports/outputs/kobert_confusion_matrix.csv`
- `logs/kobert_training_log.csv`
- `models/kobert_compatible_classifier.pt`
"""
    (REPORT_DIR / "KOBERT_SUMMARY.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    config = TransformerConfig()
    set_seed(config.seed)
    start = time.perf_counter()

    train_df, valid_df, test_df = load_split_data()
    train_df = limit_samples(train_df, config.max_train_samples, config.seed)
    valid_df = limit_samples(valid_df, config.max_valid_samples, config.seed)
    test_df = limit_samples(test_df, config.max_test_samples, config.seed)

    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        config.model_name,
        num_labels=len(LABELS),
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    train_dataset = tokenize_frame(tokenizer, train_df, config)
    valid_dataset = tokenize_frame(tokenizer, valid_df, config)
    test_dataset = tokenize_frame(tokenizer, test_df, config)
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    valid_loader = DataLoader(valid_dataset, batch_size=config.batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=False)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )

    best_valid_f1 = -1.0
    best_state = None
    log_rows = []
    for epoch in range(1, config.epochs + 1):
        model.train()
        total_loss = 0.0
        optimizer.zero_grad()
        for step, batch in enumerate(train_loader, start=1):
            labels = batch["labels"].to(device)
            inputs = {
                key: value.to(device)
                for key, value in batch.items()
                if key in {"input_ids", "attention_mask", "token_type_ids"}
            }
            outputs = model(**inputs, labels=labels)
            loss = outputs.loss / config.gradient_accumulation_steps
            loss.backward()
            if step % config.gradient_accumulation_steps == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                optimizer.zero_grad()
            total_loss += float(outputs.loss.item()) * len(labels)

        valid_true, valid_pred, valid_loss = evaluate(model, valid_loader, device)
        valid_report = classification_report(
            valid_true,
            valid_pred,
            labels=list(LABELS.keys()),
            output_dict=True,
            zero_division=0,
        )
        valid_f1 = float(valid_report["macro avg"]["f1-score"])
        log_rows.append(
            {
                "epoch": epoch,
                "train_loss": round(total_loss / len(train_df), 6),
                "valid_loss": round(valid_loss, 6),
                "valid_accuracy": round(float(accuracy_score(valid_true, valid_pred)), 6),
                "valid_macro_f1": round(valid_f1, 6),
            }
        )
        if valid_f1 > best_valid_f1:
            best_valid_f1 = valid_f1
            best_state = {key: value.cpu().clone() for key, value in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
        model.to(device)

    y_true, y_pred, _ = evaluate(model, test_loader, device)
    elapsed = time.perf_counter() - start
    config_dict = asdict(config)
    config_dict["device"] = str(device)
    config_dict["actual_train_samples"] = len(train_df)
    config_dict["actual_valid_samples"] = len(valid_df)
    config_dict["actual_test_samples"] = len(test_df)
    config_dict["best_valid_macro_f1"] = round(best_valid_f1, 6)

    row, class_df, matrix_df = metrics_row(
        "kobert_compatible_klue_roberta_small",
        y_true,
        y_pred,
        elapsed,
        config_dict,
    )
    row["best_valid_macro_f1"] = round(best_valid_f1, 6)
    row["device"] = str(device)
    metrics_df = pd.DataFrame([row])
    metrics_df.to_csv(OUTPUT_DIR / "kobert_metrics.csv", index=False)
    class_df.to_csv(OUTPUT_DIR / "kobert_classification_report.csv", index=False)
    matrix_df.to_csv(OUTPUT_DIR / "kobert_confusion_matrix.csv")
    pd.DataFrame(
        {
            "index": test_df["index"],
            "category": y_true,
            "prediction": y_pred,
        }
    ).to_csv(OUTPUT_DIR / "kobert_test_predictions.csv", index=False)
    pd.DataFrame(log_rows).to_csv(LOG_DIR / "kobert_training_log.csv", index=False)
    write_matrix_svg(
        FIGURE_DIR / "kobert_confusion_matrix.svg",
        "KoBERT-compatible Transformer Confusion Matrix",
        matrix_df,
    )

    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": config_dict,
            "labels": LABELS,
        },
        MODEL_DIR / "kobert_compatible_classifier.pt",
    )
    baseline = pd.read_csv(OUTPUT_DIR / "baseline_metrics.csv")
    write_report(config, metrics_df, baseline, len(train_df), len(valid_df), len(test_df))


if __name__ == "__main__":
    main()
