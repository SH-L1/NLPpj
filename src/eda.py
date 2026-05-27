from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports"
OUTPUT_DIR = REPORT_DIR / "outputs"

LABELS = {
    0: "인권/성평등",
    1: "문화/예술/체육/언론",
    2: "육아/교육",
}


def load_csv(name: str) -> pd.DataFrame:
    path = RAW_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required dataset: {path}")
    return pd.read_csv(path)


def text_stats(series: pd.Series) -> dict[str, float | int]:
    lengths = series.fillna("").astype(str).str.len()
    quantiles = lengths.quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    return {
        "min": int(lengths.min()),
        "mean": round(float(lengths.mean()), 2),
        "median": round(float(quantiles.loc[0.5]), 2),
        "p75": round(float(quantiles.loc[0.75]), 2),
        "p90": round(float(quantiles.loc[0.9]), 2),
        "p95": round(float(quantiles.loc[0.95]), 2),
        "p99": round(float(quantiles.loc[0.99]), 2),
        "max": int(lengths.max()),
        "empty": int((lengths == 0).sum()),
    }


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    headers = "| " + " | ".join(map(str, df.columns)) + " |"
    divider = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in df.to_numpy()]
    return "\n".join([headers, divider, *rows])


def write_bar_svg(path: Path, labels: list[str], values: list[int]) -> None:
    width, height = 820, 480
    margin_left, margin_bottom, margin_top = 80, 90, 50
    chart_width = width - margin_left - 40
    chart_height = height - margin_top - margin_bottom
    max_value = max(values)
    bar_width = chart_width / len(values) * 0.58
    gap = chart_width / len(values)

    bars = []
    for i, (label, value) in enumerate(zip(labels, values)):
        x = margin_left + i * gap + (gap - bar_width) / 2
        bar_height = chart_height * value / max_value
        y = margin_top + chart_height - bar_height
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" '
            f'height="{bar_height:.1f}" fill="#3b82f6" />'
        )
        bars.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{y - 8:.1f}" '
            f'text-anchor="middle" font-size="15">{value:,}</text>'
        )
        bars.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{height - 42}" '
            f'text-anchor="middle" font-size="15">{label}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white" />
<text x="{width / 2}" y="30" text-anchor="middle" font-size="22" font-weight="700">Category Distribution</text>
<line x1="{margin_left}" y1="{margin_top + chart_height}" x2="{width - 40}" y2="{margin_top + chart_height}" stroke="#111827" />
<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + chart_height}" stroke="#111827" />
{''.join(bars)}
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def write_histogram_svg(path: Path, values: pd.Series, bins: int = 40) -> None:
    width, height = 820, 480
    margin_left, margin_bottom, margin_top = 80, 80, 50
    chart_width = width - margin_left - 40
    chart_height = height - margin_top - margin_bottom
    min_value, max_value = int(values.min()), int(values.max())
    bin_size = max(1, (max_value - min_value) / bins)
    counts = [0] * bins
    for value in values:
        idx = min(bins - 1, int((value - min_value) / bin_size))
        counts[idx] += 1

    max_count = max(counts)
    bar_width = chart_width / bins
    bars = []
    for i, count in enumerate(counts):
        x = margin_left + i * bar_width
        bar_height = chart_height * count / max_count if max_count else 0
        y = margin_top + chart_height - bar_height
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(1, bar_width - 1):.1f}" '
            f'height="{bar_height:.1f}" fill="#10b981" />'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white" />
<text x="{width / 2}" y="30" text-anchor="middle" font-size="22" font-weight="700">Train Text Length Distribution (p99 clipped)</text>
<line x1="{margin_left}" y1="{margin_top + chart_height}" x2="{width - 40}" y2="{margin_top + chart_height}" stroke="#111827" />
<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + chart_height}" stroke="#111827" />
{''.join(bars)}
<text x="{margin_left}" y="{height - 35}" font-size="14">{min_value}</text>
<text x="{width - 45}" y="{height - 35}" text-anchor="end" font-size="14">{max_value}</text>
<text x="{width / 2}" y="{height - 18}" text-anchor="middle" font-size="14">Text length</text>
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def build_report(train: pd.DataFrame, test: pd.DataFrame) -> str:
    category_counts = (
        train["category"]
        .value_counts(dropna=False)
        .sort_index()
        .rename_axis("category")
        .reset_index(name="count")
    )
    category_counts["label"] = category_counts["category"].map(LABELS)
    category_counts["ratio"] = category_counts["count"].map(
        lambda count: f"{count / len(train) * 100:.2f}%"
    )
    category_counts = category_counts[["category", "label", "count", "ratio"]]

    missing = pd.DataFrame(
        {
            "dataset": ["train", "test"],
            "rows": [len(train), len(test)],
            "missing_data": [
                int(train["data"].isna().sum()),
                int(test["data"].isna().sum()),
            ],
            "duplicated_data": [
                int(train["data"].duplicated().sum()),
                int(test["data"].duplicated().sum()),
            ],
        }
    )

    length_summary = pd.DataFrame(
        [
            {"dataset": "train", **text_stats(train["data"])},
            {"dataset": "test", **text_stats(test["data"])},
        ]
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    figure_dir = REPORT_DIR / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    category_counts.to_csv(OUTPUT_DIR / "category_distribution.csv", index=False)
    missing.to_csv(OUTPUT_DIR / "data_quality_summary.csv", index=False)
    length_summary.to_csv(OUTPUT_DIR / "text_length_summary.csv", index=False)

    write_bar_svg(
        figure_dir / "category_distribution.svg",
        labels=category_counts["label"].tolist(),
        values=category_counts["count"].tolist(),
    )
    train_lengths = train["data"].fillna("").astype(str).str.len()
    clipped_lengths = train_lengths.clip(upper=train_lengths.quantile(0.99))
    write_histogram_svg(figure_dir / "text_length_distribution.svg", clipped_lengths)

    return f"""# 국민청원 데이터 EDA 요약

## 1. 데이터 개요

- 데이터 출처: 데이콘 청와대 청원 분류 경진대회
- 원본 위치: `data/raw/train.csv`, `data/raw/test.csv`
- 분석 실행 파일: `src/eda.py`
- 원본 CSV는 Git에 커밋하지 않는다.

## 2. 파일 구조

| 파일 | 행 수 | 컬럼 | 용도 |
| --- | ---: | --- | --- |
| `train.csv` | {len(train):,} | `{", ".join(train.columns)}` | 학습/검증/내부 테스트 |
| `test.csv` | {len(test):,} | `{", ".join(test.columns)}` | 최종 추론 또는 제출 형식 검증 |

## 3. 라벨 분포

{markdown_table(category_counts)}

라벨 분포는 세 카테고리가 거의 균등하므로, 기본 학습 단계에서는 별도의 리샘플링 없이 시작한다. 이후 모델별 클래스 성능을 확인하면서 필요하면 class weight 적용 여부를 판단한다.

- 그래프: `reports/figures/category_distribution.svg`

## 4. 결측치와 중복

{markdown_table(missing)}

학습 데이터에는 본문 결측치가 8건 존재한다. 전처리 단계에서 `data` 결측 행은 제거한다. 중복 본문은 train 637건, test 25건이므로, 완전 중복 제거 전후의 성능 차이를 비교한다.

## 5. 텍스트 길이 통계

{markdown_table(length_summary)}

train/test 모두 평균보다 중앙값이 낮고 최대 길이가 매우 길다. 장문과 극단적으로 긴 본문이 포함되어 있으므로, RNN/LSTM에서는 truncation과 장기 의존성 한계가 성능 저하 요인이 될 수 있다. KoBERT 실험에서는 `max_length`를 고정하고, 잘리는 비율을 기록한다.

- 그래프: `reports/figures/text_length_distribution.svg`

## 6. 다음 단계 전처리 결정

- 결측 본문 8건 제거
- 줄바꿈과 연속 공백 정규화
- HTML 태그, URL, 특수문자 제거
- 국민청원 도메인 불용어 후보 빈도 분석
- `min_df`, `max_df` 조합별 어휘 수와 성능 비교
"""


def main() -> None:
    train = load_csv("train.csv")
    test = load_csv("test.csv")

    required_train = {"index", "category", "data"}
    required_test = {"index", "data"}
    if set(train.columns) != required_train:
        raise ValueError(f"Unexpected train columns: {list(train.columns)}")
    if set(test.columns) != required_test:
        raise ValueError(f"Unexpected test columns: {list(test.columns)}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report(train, test)
    (REPORT_DIR / "EDA_SUMMARY.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
