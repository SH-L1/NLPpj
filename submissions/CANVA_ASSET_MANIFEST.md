# Canva 에셋 삽입 목록

Canva에서 새 발표 덱을 만든 뒤, 아래 파일을 각 슬라이드의 placeholder에 삽입한다.

## 필수 차트/이미지

| slide | placeholder | local file |
|---:|---|---|
| 1 | 프로젝트 구조 또는 데이터 예시 | `README.md` 프로젝트 구조 캡처 또는 `data/raw/train.csv` 일부 캡처 |
| 2 | 데이터 컬럼 예시 | `data/raw/train.csv` 일부 캡처 |
| 3 | 라벨 분포 또는 길이 분포 | `reports/figures/category_distribution.svg` 또는 `reports/figures/text_length_distribution.svg` |
| 5 | 불용어 제거 전후 토큰 비교 | `reports/figures/top_tokens_before_stopwords.svg`, `reports/figures/top_tokens_after_stopwords.svg` |
| 9 | 최종 Macro F1 비교 | `reports/figures/final_macro_f1_comparison.svg` |
| 10 | Transformer Confusion Matrix | `reports/figures/kobert_confusion_matrix.svg` |

## 코드 캡처 대상

| slide | source file | capture target |
|---:|---|---|
| 4 | `src/preprocess.py` | `normalize_text`, `drop_train_noise` 핵심 부분 |
| 6 | `src/train_baseline.py` | `SplitConfig`, `TfidfRfConfig`, `LstmConfig` 일부 |
| 8 | `src/train_kobert.py` | `TransformerConfig`, `AutoTokenizer`, `AutoModelForSequenceClassification`, `AdamW` |

## Canva 업로드 순서

1. Canva에서 16:9 프레젠테이션 생성
2. Data Focus 계열 또는 clean analytics 템플릿 선택
3. `CANVA_CREATE_PROMPT.md` 내용을 Canva 생성 프롬프트에 입력
4. 생성된 슬라이드 수가 11장인지 확인
5. `CANVA_FINAL_DECK_BRIEF.md`를 기준으로 문구와 수치 검수
6. 위 표의 chart/image/code capture를 placeholder에 삽입
7. 표 디자인이 세로선 없는 modern table인지 확인
8. 최종 제목이 claim형 문장인지 확인

## Canva 최종 검수 체크

- [ ] 11장 구성
- [ ] 모든 수치가 프로젝트 CSV/보고서와 일치
- [ ] 코드 슬라이드 4, 6, 8 포함
- [ ] `0.8847`, `+0.0912`, `+0.1646`가 시각적으로 강조됨
- [ ] `min_df=3`, `max_df=0.85`, `seed=42`, `max_length=160`, `batch_size=32`, `learning_rate=2e-5` 포함
- [ ] Confusion Matrix 기반 오분류 원인 설명 포함
- [ ] 표는 헤더 배경색, 세로선 없음, 얇은 가로선, 핵심 숫자 강조
- [ ] 발표자가 대본 없이 코드와 수치 근거로 설명 가능한 흐름
