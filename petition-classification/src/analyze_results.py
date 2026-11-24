from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
OUTPUT_DIR = REPORT_DIR / "outputs"
FIGURE_DIR = REPORT_DIR / "figures"

LABELS = {
    0: "인권/성평등",
    1: "문화/예술/체육/언론",
    2: "육아/교육",
}


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def load_metrics() -> pd.DataFrame:
    baseline = pd.read_csv(OUTPUT_DIR / "baseline_metrics.csv")
    kobert = pd.read_csv(OUTPUT_DIR / "kobert_metrics.csv")
    common_columns = [
        "model",
        "accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
        "weighted_f1",
        "elapsed_seconds",
        "config",
    ]
    combined = pd.concat(
        [baseline[common_columns], kobert[common_columns]],
        ignore_index=True,
    )
    combined["rank_macro_f1"] = combined["macro_f1"].rank(
        method="min", ascending=False
    ).astype(int)
    best_baseline = baseline.sort_values("macro_f1", ascending=False).iloc[0]
    transformer = kobert.iloc[0]
    improvements = []
    for _, row in combined.iterrows():
        improvements.append(
            {
                "model": row["model"],
                "macro_f1": row["macro_f1"],
                "delta_vs_best_baseline": row["macro_f1"] - best_baseline["macro_f1"],
                "delta_vs_lstm": row["macro_f1"]
                - baseline[baseline["model"] == "lstm"].iloc[0]["macro_f1"],
                "is_transformer": row["model"] == transformer["model"],
            }
        )
    pd.DataFrame(improvements).to_csv(
        OUTPUT_DIR / "model_improvement_summary.csv", index=False
    )
    combined.to_csv(OUTPUT_DIR / "final_model_comparison.csv", index=False)
    return combined


def load_matrix(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / f"{name}_confusion_matrix.csv"
    return pd.read_csv(path, index_col=0)


def matrix_long(model: str, matrix: pd.DataFrame) -> pd.DataFrame:
    rows = []
    values = matrix.to_numpy()
    for true_id in range(values.shape[0]):
        support = int(values[true_id].sum())
        correct = int(values[true_id, true_id])
        rows.append(
            {
                "model": model,
                "label_id": true_id,
                "label": LABELS[true_id],
                "support": support,
                "correct": correct,
                "wrong": support - correct,
                "recall_from_matrix": correct / support if support else 0,
            }
        )
        for pred_id in range(values.shape[1]):
            if true_id == pred_id:
                continue
            count = int(values[true_id, pred_id])
            rows.append(
                {
                    "model": model,
                    "label_id": true_id,
                    "label": LABELS[true_id],
                    "predicted_label_id": pred_id,
                    "predicted_label": LABELS[pred_id],
                    "misclassified_count": count,
                    "misclassified_ratio_in_true_label": count / support
                    if support
                    else 0,
                }
            )
    return pd.DataFrame(rows)


def analyze_confusion() -> tuple[pd.DataFrame, pd.DataFrame]:
    matrices = {
        "tfidf_random_forest": load_matrix("tfidf_random_forest"),
        "lstm": load_matrix("lstm"),
        "kobert_compatible_klue_roberta_small": load_matrix("kobert"),
    }
    recall_rows = []
    error_rows = []
    for model, matrix in matrices.items():
        values = matrix.to_numpy()
        for true_id in range(values.shape[0]):
            support = int(values[true_id].sum())
            correct = int(values[true_id, true_id])
            recall_rows.append(
                {
                    "model": model,
                    "label_id": true_id,
                    "label": LABELS[true_id],
                    "support": support,
                    "correct": correct,
                    "wrong": support - correct,
                    "recall": round(correct / support, 6),
                }
            )
            for pred_id in range(values.shape[1]):
                if true_id == pred_id:
                    continue
                count = int(values[true_id, pred_id])
                error_rows.append(
                    {
                        "model": model,
                        "true_label_id": true_id,
                        "true_label": LABELS[true_id],
                        "predicted_label_id": pred_id,
                        "predicted_label": LABELS[pred_id],
                        "count": count,
                        "ratio_in_true_label": round(count / support, 6),
                    }
                )
    recall_df = pd.DataFrame(recall_rows)
    error_df = pd.DataFrame(error_rows).sort_values(
        ["model", "count"], ascending=[True, False]
    )
    recall_df.to_csv(OUTPUT_DIR / "confusion_recall_by_label.csv", index=False)
    error_df.to_csv(OUTPUT_DIR / "confusion_error_patterns.csv", index=False)
    return recall_df, error_df


def read_preprocessing() -> tuple[pd.DataFrame, pd.DataFrame]:
    comparison = pd.read_csv(OUTPUT_DIR / "preprocessing_comparison.csv")
    vocab = pd.read_csv(OUTPUT_DIR / "vocabulary_experiments.csv")
    return comparison, vocab


def write_performance_svg(metrics: pd.DataFrame) -> None:
    data = metrics.sort_values("macro_f1")
    width, height = 850, 430
    margin_left, margin_bottom, margin_top = 260, 60, 45
    chart_width = width - margin_left - 50
    chart_height = height - margin_top - margin_bottom
    row_height = chart_height / len(data)
    bars = []
    for i, (_, row) in enumerate(data.iterrows()):
        y = margin_top + i * row_height + 10
        value = float(row["macro_f1"])
        bar_width = chart_width * value
        label = str(row["model"])
        bars.append(
            f'<text x="{margin_left - 12}" y="{y + row_height * 0.55:.1f}" '
            f'text-anchor="end" font-size="13">{label}</text>'
        )
        bars.append(
            f'<rect x="{margin_left}" y="{y:.1f}" width="{bar_width:.1f}" '
            f'height="{max(1, row_height - 18):.1f}" fill="#2563eb" />'
        )
        bars.append(
            f'<text x="{margin_left + bar_width + 8:.1f}" '
            f'y="{y + row_height * 0.55:.1f}" font-size="13">{value:.4f}</text>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white" />
<text x="{width / 2}" y="28" text-anchor="middle" font-size="22" font-weight="700">Macro F1 by Model</text>
{''.join(bars)}
<text x="{width / 2}" y="{height - 18}" text-anchor="middle" font-size="13">Higher is better</text>
</svg>
'''
    (FIGURE_DIR / "final_macro_f1_comparison.svg").write_text(svg, encoding="utf-8")


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    view = df[columns].copy()
    for column in view.columns:
        if pd.api.types.is_float_dtype(view[column]):
            view[column] = view[column].map(lambda value: f"{value:.4f}")
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in view.to_numpy()]
    return "\n".join([header, divider, *rows])


def write_report(
    metrics: pd.DataFrame,
    recall: pd.DataFrame,
    errors: pd.DataFrame,
    preprocessing: pd.DataFrame,
    vocab: pd.DataFrame,
) -> None:
    best_baseline = metrics[metrics["model"] != "kobert_compatible_klue_roberta_small"].sort_values(
        "macro_f1", ascending=False
    ).iloc[0]
    transformer = metrics[metrics["model"] == "kobert_compatible_klue_roberta_small"].iloc[0]
    delta_best = transformer["macro_f1"] - best_baseline["macro_f1"]
    delta_lstm = transformer["macro_f1"] - metrics[metrics["model"] == "lstm"].iloc[0]["macro_f1"]
    selected_vocab = vocab[vocab["selected"] == True].iloc[0]
    top_kobert_errors = errors[
        errors["model"] == "kobert_compatible_klue_roberta_small"
    ].head(3)
    report = f"""# 최종 성능 비교 및 결과 해석

## 1. 모델별 최종 성능

{markdown_table(metrics.sort_values("macro_f1", ascending=False), ["model", "accuracy", "macro_precision", "macro_recall", "macro_f1", "weighted_f1", "elapsed_seconds"])}

- 최고 베이스라인: `{best_baseline["model"]}` macro F1 `{best_baseline["macro_f1"]:.4f}`
- Transformer 계열 모델: `klue/roberta-small` macro F1 `{transformer["macro_f1"]:.4f}`
- 최고 베이스라인 대비 개선폭: `{delta_best:+.4f}`
- LSTM 대비 개선폭: `{delta_lstm:+.4f}`
- 목표 F1 0.88 달성 여부: `{transformer["macro_f1"] >= 0.88}`

성능 변화 차트는 `reports/figures/final_macro_f1_comparison.svg`에 저장했다.

## 2. Confusion Matrix 기반 오분류 분석

카테고리별 recall:

{markdown_table(recall, ["model", "label_id", "label", "support", "correct", "wrong", "recall"])}

Transformer 모델의 주요 오분류:

{markdown_table(top_kobert_errors, ["true_label", "predicted_label", "count", "ratio_in_true_label"])}

해석:

- `인권/성평등`과 `육아/교육` 사이의 오분류가 가장 크다. 두 카테고리는 학교, 아동, 보호, 제도 개선처럼 사회정책 어휘를 공유하기 때문이다.
- `문화/예술/체육/언론`은 Transformer 모델에서 recall이 가장 높다. 체육협회, 언론, 문화예술 등 고유 도메인 어휘가 비교적 명확하기 때문이다.
- RandomForest는 빠르고 안정적인 baseline이지만 문장 순서와 문맥을 반영하지 못한다.
- LSTM은 순차 모델이지만 `max_len=160` 제한과 단어 단위 토큰화 때문에 긴 청원 본문 전체 맥락을 충분히 반영하지 못했다.

## 3. 전처리 및 파라미터 효과

전처리 전후 비교:

{markdown_table(preprocessing, ["stage", "rows", "mean_length", "median_length", "vocabulary_size"])}

선택한 TF-IDF 어휘 파라미터:

- `min_df={int(selected_vocab["min_df"])}`
- `max_df={selected_vocab["max_df"]}`
- 선택 어휘 수: `{int(selected_vocab["vocabulary_size"]):,}`

해석:

- 결측/중복 제거 후 train 데이터는 39,272건으로 정리되었다.
- `min_df=3`은 극소수 문서에만 등장하는 오탈자와 고유 잡음을 줄이기 위한 선택이다.
- `max_df=0.85`는 대부분 문서에 반복되는 범용 표현을 제거하되, 사회 이슈 관련 핵심 어휘를 과도하게 버리지 않기 위한 선택이다.
- 전처리 자체가 모델 성능을 직접 보장하지는 않지만, baseline과 Transformer가 같은 정제 데이터에서 비교되도록 실험 조건을 통제했다.

## 4. Transformer 성능 개선 해석

`klue/roberta-small`은 KoBERT 호환 한국어 Transformer 실험군으로, subword tokenization과 self-attention을 사용한다. 이 구조는 국민청원처럼 문장이 길고 구어체가 섞인 텍스트에서 다음 이점을 갖는다.

- 단어 단위 토큰화보다 한국어 어미, 조사, 복합어를 더 유연하게 처리한다.
- self-attention을 통해 문장 앞뒤의 주요 단서를 동시에 참조한다.
- 사전학습된 한국어 표현 지식을 활용하므로 작은 task-specific 데이터에서도 baseline보다 높은 성능을 낸다.
- 실제 결과에서도 macro F1이 최고 baseline 대비 `{delta_best:+.4f}` 개선되었다.

## 5. 한계와 후속 개선

- `monologg/distilkobert`는 tokenizer 호환 문제로 직접 사용하지 못했고, `klue/roberta-small`로 대체했다.
- max length 160을 넘는 긴 본문은 여전히 일부 잘린다.
- 국민청원 라벨은 사회 이슈가 겹치는 경우가 많아 `인권/성평등`과 `육아/교육` 사이 혼동이 남아 있다.
- 다음 단계에서는 긴 본문을 문단 단위로 나누어 예측을 앙상블하거나, 더 큰 한국어 사전학습 모델을 비교할 수 있다.
"""
    (REPORT_DIR / "FINAL_ANALYSIS.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    metrics = load_metrics()
    recall, errors = analyze_confusion()
    preprocessing, vocab = read_preprocessing()
    write_performance_svg(metrics)
    write_report(metrics, recall, errors, preprocessing, vocab)


if __name__ == "__main__":
    main()
