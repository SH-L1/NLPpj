from __future__ import annotations

import html
import re
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
CONFIG_DIR = ROOT / "configs"
REPORT_DIR = ROOT / "reports"
OUTPUT_DIR = REPORT_DIR / "outputs"
FIGURE_DIR = REPORT_DIR / "figures"

STOPWORDS_PATH = CONFIG_DIR / "stopwords_petition.txt"
SELECTED_MIN_DF = 3
SELECTED_MAX_DF = 0.85
TOKEN_PATTERN = re.compile(r"[가-힣A-Za-z0-9]{2,}")
DOMAIN_STOPWORD_EXAMPLES = ["대통령님", "청원합니다", "부탁드립니다", "간곡히"]


def load_stopwords(path: Path = STOPWORDS_PATH) -> set[str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing stopword file: {path}")
    stopwords: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            stopwords.add(value.lower())
    return stopwords


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def remove_stopwords(tokens: list[str], stopwords: set[str]) -> list[str]:
    return [token for token in tokens if token not in stopwords]


def preprocess_frame(df: pd.DataFrame, stopwords: set[str]) -> pd.DataFrame:
    result = df.copy()
    result["raw_text"] = result["data"]
    result["clean_text"] = result["data"].map(normalize_text)
    result["tokens_before_stopwords"] = result["clean_text"].map(tokenize)
    result["tokens"] = result["tokens_before_stopwords"].map(
        lambda tokens: remove_stopwords(tokens, stopwords)
    )
    result["token_text"] = result["tokens"].map(" ".join)
    result["raw_length"] = result["raw_text"].fillna("").astype(str).str.len()
    result["clean_length"] = result["clean_text"].str.len()
    result["token_count"] = result["tokens"].map(len)
    return result


def drop_train_noise(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    before_rows = len(df)
    missing_rows = int((df["clean_text"].str.len() == 0).sum())
    no_missing = df[df["clean_text"].str.len() > 0].copy()
    duplicated_rows = int(no_missing.duplicated(subset=["clean_text"]).sum())
    deduped = no_missing.drop_duplicates(subset=["clean_text"], keep="first").copy()
    removed_rows = before_rows - len(deduped)
    return deduped, {
        "before_rows": before_rows,
        "missing_rows_removed": missing_rows,
        "duplicate_rows_removed": duplicated_rows,
        "total_rows_removed": removed_rows,
        "after_rows": len(deduped),
    }


def cleaning_pattern_counts(df: pd.DataFrame) -> pd.DataFrame:
    raw = df["data"].fillna("").astype(str)
    rows = [
        {
            "pattern": "html_tag",
            "rows": int(raw.str.contains(r"<[^>]+>", regex=True).sum()),
        },
        {
            "pattern": "url",
            "rows": int(raw.str.contains(r"https?://\S+|www\.\S+", regex=True).sum()),
        },
        {
            "pattern": "email",
            "rows": int(
                raw.str.contains(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", regex=True).sum()
            ),
        },
        {
            "pattern": "newline_or_tab",
            "rows": int(raw.str.contains(r"[\r\n\t]+", regex=True).sum()),
        },
        {
            "pattern": "special_character",
            "rows": int(raw.str.contains(r"[^0-9A-Za-z가-힣\s]", regex=True).sum()),
        },
    ]
    return pd.DataFrame(rows)


def top_tokens(series: pd.Series, top_n: int = 30) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    for tokens in series:
        counter.update(tokens)
    return pd.DataFrame(counter.most_common(top_n), columns=["token", "count"])


def token_counter(series: pd.Series) -> Counter[str]:
    counter: Counter[str] = Counter()
    for tokens in series:
        counter.update(tokens)
    return counter


def text_length_stats(name: str, df: pd.DataFrame, column: str) -> dict[str, object]:
    lengths = df[column].fillna("").astype(str).str.len()
    return {
        "dataset": name,
        "column": column,
        "rows": len(df),
        "mean_length": round(float(lengths.mean()), 2),
        "median_length": round(float(lengths.median()), 2),
        "max_length": int(lengths.max()),
        "empty_rows": int((lengths == 0).sum()),
    }


def document_frequency(tokens_series: pd.Series) -> Counter[str]:
    counter: Counter[str] = Counter()
    for tokens in tokens_series:
        counter.update(set(tokens))
    return counter


def vocabulary_experiments(tokens_series: pd.Series) -> pd.DataFrame:
    doc_count = len(tokens_series)
    df_counter = document_frequency(tokens_series)
    rows = []
    for min_df in [2, 3, 5, 10]:
        for max_df in [0.50, 0.70, 0.85, 0.95]:
            max_doc_count = int(doc_count * max_df)
            vocabulary_size = sum(
                1 for count in df_counter.values() if min_df <= count <= max_doc_count
            )
            rows.append(
                {
                    "min_df": min_df,
                    "max_df": max_df,
                    "max_doc_count": max_doc_count,
                    "vocabulary_size": vocabulary_size,
                    "selected": min_df == SELECTED_MIN_DF and max_df == SELECTED_MAX_DF,
                }
            )
    return pd.DataFrame(rows)


def write_stopword_coverage(
    before_counter: Counter[str], after_counter: Counter[str], stopwords: set[str]
) -> pd.DataFrame:
    rows = []
    for word in sorted(stopwords):
        before_count = before_counter.get(word, 0)
        if before_count:
            rows.append(
                {
                    "stopword": word,
                    "before_count": before_count,
                    "after_count": after_counter.get(word, 0),
                }
            )
    return pd.DataFrame(rows).sort_values("before_count", ascending=False)


def write_bar_svg(path: Path, title: str, df: pd.DataFrame) -> None:
    data = df.head(20)
    width, height = 920, 620
    margin_left, margin_right, margin_top, margin_bottom = 170, 40, 55, 45
    chart_width = width - margin_left - margin_right
    chart_height = height - margin_top - margin_bottom
    max_value = int(data["count"].max()) if not data.empty else 1
    row_height = chart_height / max(len(data), 1)
    bars: list[str] = []
    for i, row in data.reset_index(drop=True).iterrows():
        y = margin_top + i * row_height + 4
        bar_width = chart_width * int(row["count"]) / max_value
        label = str(row["token"])
        count = int(row["count"])
        bars.append(
            f'<text x="{margin_left - 10}" y="{y + row_height * 0.62:.1f}" '
            f'text-anchor="end" font-size="14">{label}</text>'
        )
        bars.append(
            f'<rect x="{margin_left}" y="{y:.1f}" width="{bar_width:.1f}" '
            f'height="{max(1, row_height - 8):.1f}" fill="#2563eb" />'
        )
        bars.append(
            f'<text x="{margin_left + bar_width + 8:.1f}" '
            f'y="{y + row_height * 0.62:.1f}" font-size="13">{count:,}</text>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white" />
<text x="{width / 2}" y="32" text-anchor="middle" font-size="22" font-weight="700">{title}</text>
{''.join(bars)}
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def build_report(
    train_raw: pd.DataFrame,
    train_clean: pd.DataFrame,
    test_clean: pd.DataFrame,
    noise_stats: dict[str, int],
    before_freq: pd.DataFrame,
    after_freq: pd.DataFrame,
    vocab: pd.DataFrame,
    comparison: pd.DataFrame,
    pattern_counts: pd.DataFrame,
    domain_examples: pd.DataFrame,
) -> str:
    selected_vocab = vocab[vocab["selected"]].iloc[0]
    return f"""# 도메인 맞춤형 전처리 요약

## 1. 전처리 목적

국민청원 본문에서 카테고리 분류에 불필요한 노이즈를 제거하고, 머신러닝 베이스라인과 KoBERT 실험에 재사용할 수 있는 정제 데이터를 생성했다.

## 2. 적용한 정제 규칙

- HTML 태그 제거
- URL 제거
- 이메일 형식 문자열 제거
- 줄바꿈, 탭, 연속 공백을 단일 공백으로 정규화
- 한글, 영어, 숫자, 공백을 제외한 특수문자 제거
- 결측 본문 제거
- 학습 데이터의 완전 중복 본문 제거
- 국민청원 도메인 불용어 제거

## 3. 행 수 변화

| 항목 | 값 |
| --- | ---: |
| train 원본 행 수 | {noise_stats["before_rows"]:,} |
| 결측 본문 제거 | {noise_stats["missing_rows_removed"]:,} |
| 중복 본문 제거 | {noise_stats["duplicate_rows_removed"]:,} |
| 총 제거 행 수 | {noise_stats["total_rows_removed"]:,} |
| train 정제 후 행 수 | {noise_stats["after_rows"]:,} |
| test 정제 후 행 수 | {len(test_clean):,} |

test 데이터는 제출용 `index` 보존이 필요하므로 행 제거 없이 동일한 텍스트 정제만 적용했다.

## 4. 노이즈 패턴 확인

| 패턴 | 포함 행 수 |
| --- | ---: |
{chr(10).join(f'| {row["pattern"]} | {int(row["rows"]):,} |' for _, row in pattern_counts.iterrows())}

위 패턴은 정규표현식 기반 정제 규칙의 적용 대상이다. 특히 줄바꿈과 특수문자는 국민청원 본문에 광범위하게 포함되어 있어 정규화가 필요하다.

## 5. 전처리 전후 비교

| 단계 | 행 수 | 평균 길이 | 중앙값 길이 | 어휘 수 |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(f'| {row["stage"]} | {int(row["rows"]):,} | {float(row["mean_length"]):.2f} | {float(row["median_length"]):.2f} | {int(row["vocabulary_size"]):,} |' for _, row in comparison.iterrows())}

세부 CSV는 `reports/outputs/preprocessing_comparison.csv`에 저장했다.

## 6. 텍스트 길이 변화

| 데이터 | 원본 평균 길이 | 정제 후 평균 길이 | 원본 중앙값 | 정제 후 중앙값 |
| --- | ---: | ---: | ---: | ---: |
| train | {train_raw["data"].fillna("").astype(str).str.len().mean():.2f} | {train_clean["clean_length"].mean():.2f} | {train_raw["data"].fillna("").astype(str).str.len().median():.2f} | {train_clean["clean_length"].median():.2f} |
| test | - | {test_clean["clean_length"].mean():.2f} | - | {test_clean["clean_length"].median():.2f} |

## 7. 상위 토큰 비교

- 불용어 제거 전 상위 토큰: `reports/outputs/top_tokens_before_stopwords.csv`
- 불용어 제거 후 상위 토큰: `reports/outputs/top_tokens_after_stopwords.csv`
- 불용어 커버리지: `reports/outputs/stopword_coverage.csv`
- 시각화: `reports/figures/top_tokens_before_stopwords.svg`, `reports/figures/top_tokens_after_stopwords.svg`

도메인 특화 불용어 예시:

| 불용어 | 제거 전 빈도 | 제거 후 빈도 |
| --- | ---: | ---: |
{chr(10).join(f'| {row["stopword"]} | {int(row["before_count"]):,} | {int(row["after_count"]):,} |' for _, row in domain_examples.iterrows())}

## 8. `min_df` / `max_df` 실험 결과

- 전체 실험표: `reports/outputs/vocabulary_experiments.csv`
- 선택값: `min_df={SELECTED_MIN_DF}`, `max_df={SELECTED_MAX_DF}`
- 선택 어휘 수: {int(selected_vocab["vocabulary_size"]):,}

선택 근거는 다음과 같다.

- `min_df=3`: 한두 문서에만 등장하는 오탈자, 고유명사, 잡음을 줄이면서 국민청원 도메인 표현은 유지한다.
- `max_df=0.85`: 대부분 문서에 반복되는 범용 표현을 제거하되, 세 카테고리 모두에 걸쳐 의미가 있는 정책/사회 이슈 단어까지 과도하게 제거하지 않는다.
- 라벨 분포가 균등하므로, 전처리 단계에서는 리샘플링보다 어휘 품질 관리에 우선순위를 둔다.

## 9. 생성된 정제 데이터

- `data/processed/train_clean.csv`
- `data/processed/test_clean.csv`

정제 데이터는 재생성 가능한 산출물이므로 Git에는 커밋하지 않는다. 재생성 명령은 다음과 같다.

```bash
python src/preprocess.py
```
"""


def main() -> None:
    stopwords = load_stopwords()
    train_raw = pd.read_csv(RAW_DIR / "train.csv")
    test_raw = pd.read_csv(RAW_DIR / "test.csv")

    train_preprocessed = preprocess_frame(train_raw, stopwords)
    test_preprocessed = preprocess_frame(test_raw, stopwords)
    train_clean, noise_stats = drop_train_noise(train_preprocessed)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    train_columns = [
        "index",
        "category",
        "raw_text",
        "clean_text",
        "token_text",
        "raw_length",
        "clean_length",
        "token_count",
    ]
    test_columns = [
        "index",
        "raw_text",
        "clean_text",
        "token_text",
        "raw_length",
        "clean_length",
        "token_count",
    ]
    train_clean[train_columns].to_csv(PROCESSED_DIR / "train_clean.csv", index=False)
    test_preprocessed[test_columns].to_csv(
        PROCESSED_DIR / "test_clean.csv", index=False
    )

    before_freq = top_tokens(train_preprocessed["tokens_before_stopwords"])
    after_freq = top_tokens(train_clean["tokens"])
    before_counter = token_counter(train_preprocessed["tokens_before_stopwords"])
    after_counter = token_counter(train_clean["tokens"])
    vocab = vocabulary_experiments(train_clean["tokens"])
    stopword_coverage = write_stopword_coverage(before_counter, after_counter, stopwords)
    pattern_counts = cleaning_pattern_counts(train_raw)
    domain_examples = pd.DataFrame(
        [
            {
                "stopword": word,
                "before_count": before_counter.get(word, 0),
                "after_count": after_counter.get(word, 0),
            }
            for word in DOMAIN_STOPWORD_EXAMPLES
        ]
    )

    comparison = pd.DataFrame(
        [
            {
                "stage": "raw_tokenized",
                "rows": len(train_preprocessed),
                "mean_length": train_preprocessed["raw_length"].mean(),
                "median_length": train_preprocessed["raw_length"].median(),
                "vocabulary_size": len(before_counter),
            },
            {
                "stage": "cleaned_stopwords_removed",
                "rows": len(train_clean),
                "mean_length": train_clean["clean_length"].mean(),
                "median_length": train_clean["clean_length"].median(),
                "vocabulary_size": len(after_counter),
            },
        ]
    )

    summary_rows = [
        text_length_stats("train_raw", train_raw, "data"),
        text_length_stats("train_clean", train_clean, "clean_text"),
        text_length_stats("test_clean", test_preprocessed, "clean_text"),
    ]
    pd.DataFrame(summary_rows).to_csv(
        OUTPUT_DIR / "preprocessing_summary.csv", index=False
    )
    pd.DataFrame([noise_stats]).to_csv(OUTPUT_DIR / "preprocessing_noise.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / "preprocessing_comparison.csv", index=False)
    pattern_counts.to_csv(OUTPUT_DIR / "cleaning_pattern_counts.csv", index=False)
    before_freq.to_csv(OUTPUT_DIR / "top_tokens_before_stopwords.csv", index=False)
    after_freq.to_csv(OUTPUT_DIR / "top_tokens_after_stopwords.csv", index=False)
    vocab.to_csv(OUTPUT_DIR / "vocabulary_experiments.csv", index=False)
    stopword_coverage.to_csv(OUTPUT_DIR / "stopword_coverage.csv", index=False)
    domain_examples.to_csv(OUTPUT_DIR / "domain_stopword_examples.csv", index=False)

    write_bar_svg(
        FIGURE_DIR / "top_tokens_before_stopwords.svg",
        "Top Tokens Before Stopword Removal",
        before_freq,
    )
    write_bar_svg(
        FIGURE_DIR / "top_tokens_after_stopwords.svg",
        "Top Tokens After Stopword Removal",
        after_freq,
    )

    report = build_report(
        train_raw=train_raw,
        train_clean=train_clean,
        test_clean=test_preprocessed,
        noise_stats=noise_stats,
        before_freq=before_freq,
        after_freq=after_freq,
        vocab=vocab,
        comparison=comparison,
        pattern_counts=pattern_counts,
        domain_examples=domain_examples,
    )
    (REPORT_DIR / "PREPROCESSING_SUMMARY.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
