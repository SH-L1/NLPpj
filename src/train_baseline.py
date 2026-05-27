from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, Dataset


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
class SplitConfig:
    seed: int = SEED
    train_ratio: float = 0.70
    valid_ratio: float = 0.15
    test_ratio: float = 0.15
    stratify_column: str = "category"


@dataclass(frozen=True)
class TfidfRfConfig:
    max_features: int = 20000
    min_df: int = 3
    max_df: float = 0.85
    ngram_range: tuple[int, int] = (1, 2)
    n_estimators: int = 120
    max_depth: int | None = None
    min_samples_leaf: int = 2
    n_jobs: int = -1
    random_state: int = SEED


@dataclass(frozen=True)
class LstmConfig:
    vocab_size: int = 20000
    max_len: int = 160
    embedding_dim: int = 64
    hidden_dim: int = 64
    num_layers: int = 1
    batch_size: int = 256
    epochs: int = 5
    learning_rate: float = 0.001
    min_token_freq: int = 2
    random_state: int = SEED


class PetitionDataset(Dataset):
    def __init__(self, sequences: np.ndarray, lengths: np.ndarray, labels: np.ndarray) -> None:
        self.sequences = torch.tensor(sequences, dtype=torch.long)
        self.lengths = torch.tensor(lengths, dtype=torch.long)
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.sequences[index], self.lengths[index], self.labels[index]


class LstmClassifier(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        hidden_dim: int,
        num_layers: int,
        num_classes: int,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.dropout = nn.Dropout(0.25)
        self.classifier = nn.Linear(hidden_dim, num_classes)

    def forward(self, tokens: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(tokens)
        packed = nn.utils.rnn.pack_padded_sequence(
            embedded,
            lengths.cpu(),
            batch_first=True,
            enforce_sorted=False,
        )
        _, (hidden, _) = self.lstm(packed)
        last_hidden = hidden[-1]
        return self.classifier(self.dropout(last_hidden))


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


def load_data() -> pd.DataFrame:
    path = PROCESSED_DIR / "train_clean.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `python src/preprocess.py` before baseline training."
        )
    df = pd.read_csv(path)
    required = {"index", "category", "clean_text", "token_text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {path}: {sorted(missing)}")
    df["token_text"] = df["token_text"].fillna("")
    df["clean_text"] = df["clean_text"].fillna("")
    return df


def split_data(df: pd.DataFrame, config: SplitConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df, temp_df = train_test_split(
        df,
        train_size=config.train_ratio,
        random_state=config.seed,
        stratify=df[config.stratify_column],
    )
    relative_valid_size = config.valid_ratio / (config.valid_ratio + config.test_ratio)
    valid_df, test_df = train_test_split(
        temp_df,
        train_size=relative_valid_size,
        random_state=config.seed,
        stratify=temp_df[config.stratify_column],
    )
    return (
        train_df.sort_values("index").reset_index(drop=True),
        valid_df.sort_values("index").reset_index(drop=True),
        test_df.sort_values("index").reset_index(drop=True),
    )


def save_split_artifacts(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    config: SplitConfig,
) -> None:
    split_rows = []
    for split_name, split_df in [
        ("train", train_df),
        ("valid", valid_df),
        ("test", test_df),
    ]:
        for index in split_df["index"].tolist():
            split_rows.append({"index": int(index), "split": split_name})
    pd.DataFrame(split_rows).to_csv(PROCESSED_DIR / "split_indices.csv", index=False)

    summary_rows = []
    for split_name, split_df in [
        ("train", train_df),
        ("valid", valid_df),
        ("test", test_df),
    ]:
        counts = split_df["category"].value_counts().sort_index().to_dict()
        row = {"split": split_name, "rows": len(split_df)}
        for label_id, label_name in LABELS.items():
            row[f"{label_id}_{label_name}"] = int(counts.get(label_id, 0))
        summary_rows.append(row)
    pd.DataFrame(summary_rows).to_csv(OUTPUT_DIR / "split_summary.csv", index=False)
    (OUTPUT_DIR / "split_config.json").write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def classification_metrics(
    model_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    elapsed_seconds: float,
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
        "elapsed_seconds": round(elapsed_seconds, 2),
        "config": json.dumps(config, ensure_ascii=False),
    }
    class_rows = []
    for label_id, label_name in LABELS.items():
        metrics = report[label_name]
        class_rows.append(
            {
                "model": model_name,
                "label_id": label_id,
                "label": label_name,
                "precision": round(float(metrics["precision"]), 6),
                "recall": round(float(metrics["recall"]), 6),
                "f1": round(float(metrics["f1-score"]), 6),
                "support": int(metrics["support"]),
            }
        )
    matrix = confusion_matrix(y_true, y_pred, labels=list(LABELS.keys()))
    matrix_df = pd.DataFrame(
        matrix,
        index=[f"true_{i}_{LABELS[i]}" for i in LABELS],
        columns=[f"pred_{i}_{LABELS[i]}" for i in LABELS],
    )
    return row, pd.DataFrame(class_rows), matrix_df


def train_tfidf_random_forest(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    config: TfidfRfConfig,
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    start = time.perf_counter()
    vectorizer = TfidfVectorizer(
        max_features=config.max_features,
        min_df=config.min_df,
        max_df=config.max_df,
        ngram_range=config.ngram_range,
        token_pattern=r"(?u)\b\w+\b",
    )
    x_train = vectorizer.fit_transform(train_df["token_text"])
    x_valid = vectorizer.transform(valid_df["token_text"])
    x_test = vectorizer.transform(test_df["token_text"])
    model = RandomForestClassifier(
        n_estimators=config.n_estimators,
        max_depth=config.max_depth,
        min_samples_leaf=config.min_samples_leaf,
        n_jobs=config.n_jobs,
        random_state=config.random_state,
        class_weight="balanced",
    )
    model.fit(x_train, train_df["category"])
    valid_pred = model.predict(x_valid)
    test_pred = model.predict(x_test)
    elapsed = time.perf_counter() - start

    pd.DataFrame(
        {
            "index": valid_df["index"],
            "category": valid_df["category"],
            "prediction": valid_pred,
        }
    ).to_csv(OUTPUT_DIR / "tfidf_random_forest_valid_predictions.csv", index=False)
    pd.DataFrame(
        {
            "index": test_df["index"],
            "category": test_df["category"],
            "prediction": test_pred,
        }
    ).to_csv(OUTPUT_DIR / "tfidf_random_forest_test_predictions.csv", index=False)

    row, class_df, matrix_df = classification_metrics(
        "tfidf_random_forest",
        test_df["category"].to_numpy(),
        test_pred,
        elapsed,
        asdict(config),
    )
    row["valid_accuracy"] = round(float(accuracy_score(valid_df["category"], valid_pred)), 6)
    row["vectorizer_vocabulary_size"] = len(vectorizer.vocabulary_)
    return row, class_df, matrix_df


def build_vocab(texts: pd.Series, config: LstmConfig) -> dict[str, int]:
    counter: dict[str, int] = {}
    for text in texts:
        for token in str(text).split():
            counter[token] = counter.get(token, 0) + 1
    filtered = [
        (token, count)
        for token, count in counter.items()
        if count >= config.min_token_freq
    ]
    filtered.sort(key=lambda item: (-item[1], item[0]))
    # 0 is padding, 1 is unknown.
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for token, _ in filtered[: config.vocab_size - 2]:
        vocab[token] = len(vocab)
    return vocab


def encode_text(text: str, vocab: dict[str, int], max_len: int) -> tuple[list[int], int]:
    ids = [vocab.get(token, 1) for token in str(text).split()[:max_len]]
    length = max(1, len(ids))
    if len(ids) < max_len:
        ids.extend([0] * (max_len - len(ids)))
    return ids, length


def make_sequences(
    df: pd.DataFrame, vocab: dict[str, int], config: LstmConfig
) -> tuple[np.ndarray, np.ndarray]:
    encoded = [encode_text(text, vocab, config.max_len) for text in df["token_text"]]
    sequences = np.array([item[0] for item in encoded], dtype=np.int64)
    lengths = np.array([item[1] for item in encoded], dtype=np.int64)
    return sequences, lengths


def evaluate_lstm(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, float]:
    model.eval()
    all_labels: list[np.ndarray] = []
    all_preds: list[np.ndarray] = []
    total_loss = 0.0
    criterion = nn.CrossEntropyLoss()
    with torch.no_grad():
        for tokens, lengths, labels in loader:
            tokens = tokens.to(device)
            lengths = lengths.to(device)
            labels = labels.to(device)
            logits = model(tokens, lengths)
            loss = criterion(logits, labels)
            total_loss += float(loss.item()) * len(labels)
            preds = torch.argmax(logits, dim=1)
            all_labels.append(labels.cpu().numpy())
            all_preds.append(preds.cpu().numpy())
    y_true = np.concatenate(all_labels)
    y_pred = np.concatenate(all_preds)
    return y_true, y_pred, total_loss / len(y_true)


def train_lstm(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    config: LstmConfig,
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    start = time.perf_counter()
    set_seed(config.random_state)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vocab = build_vocab(train_df["token_text"], config)
    train_sequences, train_lengths = make_sequences(train_df, vocab, config)
    valid_sequences, valid_lengths = make_sequences(valid_df, vocab, config)
    test_sequences, test_lengths = make_sequences(test_df, vocab, config)

    train_loader = DataLoader(
        PetitionDataset(train_sequences, train_lengths, train_df["category"].to_numpy()),
        batch_size=config.batch_size,
        shuffle=True,
    )
    valid_loader = DataLoader(
        PetitionDataset(valid_sequences, valid_lengths, valid_df["category"].to_numpy()),
        batch_size=config.batch_size,
        shuffle=False,
    )
    test_loader = DataLoader(
        PetitionDataset(test_sequences, test_lengths, test_df["category"].to_numpy()),
        batch_size=config.batch_size,
        shuffle=False,
    )
    model = LstmClassifier(
        vocab_size=len(vocab),
        embedding_dim=config.embedding_dim,
        hidden_dim=config.hidden_dim,
        num_layers=config.num_layers,
        num_classes=len(LABELS),
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = nn.CrossEntropyLoss()

    epoch_rows = []
    best_valid_f1 = -1.0
    best_state = None
    for epoch in range(1, config.epochs + 1):
        model.train()
        total_loss = 0.0
        for tokens, lengths, labels in train_loader:
            tokens = tokens.to(device)
            lengths = lengths.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits = model(tokens, lengths)
            loss = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += float(loss.item()) * len(labels)

        valid_true, valid_pred, valid_loss = evaluate_lstm(model, valid_loader, device)
        valid_report = classification_report(
            valid_true,
            valid_pred,
            labels=list(LABELS.keys()),
            output_dict=True,
            zero_division=0,
        )
        valid_f1 = float(valid_report["macro avg"]["f1-score"])
        epoch_rows.append(
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
    y_true, y_pred, _ = evaluate_lstm(model, test_loader, device)
    elapsed = time.perf_counter() - start

    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": asdict(config),
            "vocab_size": len(vocab),
            "labels": LABELS,
        },
        MODEL_DIR / "baseline_lstm.pt",
    )
    pd.DataFrame(
        {
            "index": test_df["index"],
            "category": test_df["category"],
            "prediction": y_pred,
        }
    ).to_csv(OUTPUT_DIR / "lstm_test_predictions.csv", index=False)
    epoch_df = pd.DataFrame(epoch_rows)
    epoch_df.to_csv(LOG_DIR / "lstm_training_log.csv", index=False)

    config_dict = asdict(config)
    config_dict["device"] = str(device)
    config_dict["actual_vocab_size"] = len(vocab)
    row, class_df, matrix_df = classification_metrics(
        "lstm",
        y_true,
        y_pred,
        elapsed,
        config_dict,
    )
    row["best_valid_macro_f1"] = round(best_valid_f1, 6)
    row["actual_vocab_size"] = len(vocab)
    row["device"] = str(device)
    return row, class_df, matrix_df, epoch_df


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


def write_report(metrics_df: pd.DataFrame, split_summary: pd.DataFrame) -> None:
    metrics_view = metrics_df[
        [
            "model",
            "accuracy",
            "macro_precision",
            "macro_recall",
            "macro_f1",
            "weighted_f1",
            "elapsed_seconds",
        ]
    ]
    rows = "\n".join(
        "| "
        + " | ".join(
            [
                str(row["model"]),
                f'{row["accuracy"]:.4f}',
                f'{row["macro_precision"]:.4f}',
                f'{row["macro_recall"]:.4f}',
                f'{row["macro_f1"]:.4f}',
                f'{row["weighted_f1"]:.4f}',
                f'{row["elapsed_seconds"]:.2f}',
            ]
        )
        + " |"
        for _, row in metrics_view.iterrows()
    )
    split_rows = "\n".join(
        "| " + " | ".join(map(str, row)) + " |"
        for row in split_summary.to_numpy()
    )
    split_header = "| " + " | ".join(split_summary.columns) + " |"
    split_divider = "| " + " | ".join(["---"] * len(split_summary.columns)) + " |"

    report = f"""# 베이스라인 모델 학습 결과

## 1. 목적

KoBERT 파인튜닝 전 비교 기준을 만들기 위해 동일한 데이터 분할에서 TF-IDF 기반 Random Forest와 교재 수준의 LSTM 모델을 학습했다.

## 2. 데이터 분할

- Seed: `{SEED}`
- Split: train 70%, validation 15%, test 15%
- Stratified split 기준: `category`
- KoBERT 단계에서도 같은 `data/processed/split_indices.csv`를 사용한다.

{split_header}
{split_divider}
{split_rows}

## 3. 모델별 성능

| model | accuracy | macro precision | macro recall | macro F1 | weighted F1 | elapsed seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{rows}

세부 클래스별 성능은 `reports/outputs/baseline_classification_report.csv`에 저장했다.

## 4. 산출물

- `reports/outputs/baseline_metrics.csv`
- `reports/outputs/baseline_classification_report.csv`
- `reports/outputs/tfidf_random_forest_confusion_matrix.csv`
- `reports/outputs/lstm_confusion_matrix.csv`
- `logs/lstm_training_log.csv`
- `models/baseline_lstm.pt`

## 5. RNN/LSTM 한계 분석

- LSTM은 입력을 순차적으로 처리하므로 긴 청원 본문에서 앞부분의 맥락이 뒤쪽까지 안정적으로 전달되기 어렵다.
- 본 프로젝트에서는 `max_len=160`으로 입력을 제한했다. 평균 길이는 500자 이상이고 최대 길이는 수만 자이므로, 긴 본문은 뒷부분 정보가 잘린다.
- 단어 단위 토큰화와 작은 임베딩 차원만 사용했기 때문에 한국어 조사, 어미, 띄어쓰기 노이즈를 충분히 반영하지 못한다.
- TF-IDF Random Forest는 단어 출현 패턴을 빠르게 학습하지만 문장 순서와 문맥을 직접 이해하지 못한다.
- 다음 단계의 KoBERT는 subword tokenization과 self-attention을 사용하므로 장문 문맥과 한국어 표현을 더 잘 반영할 수 있는 실험군이다.
"""
    (REPORT_DIR / "BASELINE_SUMMARY.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    set_seed(SEED)
    split_config = SplitConfig()
    df = load_data()
    train_df, valid_df, test_df = split_data(df, split_config)
    save_split_artifacts(train_df, valid_df, test_df, split_config)

    metrics_rows: list[dict[str, object]] = []
    class_reports: list[pd.DataFrame] = []

    rf_row, rf_class, rf_matrix = train_tfidf_random_forest(
        train_df,
        valid_df,
        test_df,
        TfidfRfConfig(),
    )
    metrics_rows.append(rf_row)
    class_reports.append(rf_class)
    rf_matrix.to_csv(OUTPUT_DIR / "tfidf_random_forest_confusion_matrix.csv")
    write_matrix_svg(
        FIGURE_DIR / "tfidf_random_forest_confusion_matrix.svg",
        "TF-IDF Random Forest Confusion Matrix",
        rf_matrix,
    )

    lstm_row, lstm_class, lstm_matrix, _ = train_lstm(
        train_df,
        valid_df,
        test_df,
        LstmConfig(),
    )
    metrics_rows.append(lstm_row)
    class_reports.append(lstm_class)
    lstm_matrix.to_csv(OUTPUT_DIR / "lstm_confusion_matrix.csv")
    write_matrix_svg(
        FIGURE_DIR / "lstm_confusion_matrix.svg",
        "LSTM Confusion Matrix",
        lstm_matrix,
    )

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df.to_csv(OUTPUT_DIR / "baseline_metrics.csv", index=False)
    pd.concat(class_reports, ignore_index=True).to_csv(
        OUTPUT_DIR / "baseline_classification_report.csv", index=False
    )
    split_summary = pd.read_csv(OUTPUT_DIR / "split_summary.csv")
    write_report(metrics_df, split_summary)


if __name__ == "__main__":
    main()
