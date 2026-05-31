# Canva 최종 발표 덱 제작 브리프

## 1. 제작 목표

국민청원 장문 텍스트 분류 NLP 프로젝트를 Canva에서 처음부터 다시 제작한다. 발표자는 대본을 읽는 방식이 아니라, 화면에 보이는 코드 흐름과 실험 근거를 바탕으로 교수님 질문에 직접 답할 수 있어야 한다.

핵심 메시지:

> 국민청원 장문 텍스트를 전처리부터 Transformer 파인튜닝까지 로컬 환경에서 재현 가능한 End-to-End 파이프라인으로 구현했고, macro F1 0.8847로 목표 성능을 달성했다.

반드시 반영할 교수님 요구사항:

- 코드 흐름을 파일 단위로 설명할 수 있어야 한다.
- 전처리 근거를 설명해야 한다.
- `min_df=3`, `max_df=0.85`, `seed=42`, `max_length=160`, `batch_size=32`, `learning_rate=2e-5` 선택 이유를 설명해야 한다.
- RNN/LSTM 한계와 Transformer 도입 이유를 장문 한국어 텍스트 관점에서 설명해야 한다.
- 성능표와 Confusion Matrix를 보고 모델 장단점과 오분류 원인을 설명해야 한다.
- 발표는 5분 이내 핵심 흐름으로 구성한다.

## 2. Canva 디자인 시스템

Canva 테마 방향:

- 스타일명: Data Focus
- 무드: 데이터 중심, 분석형, 교수 평가 대응형, 신뢰감 있는 연구 발표
- 레이아웃: Split 기반이지만 카드형, 다단형, KPI rail, 고급 표, 코드 패널을 섞어 단조로움을 피한다.
- 금지: 긴 줄글 박스, 기본 검은 테두리 표, 의미 없는 장식, 과도한 아이콘, 단색 위주의 밋밋한 슬라이드

색상:

- Background: `#F7F4EE`
- Panel: `#FBFAF6`
- Ink: `#17212B`
- Muted text: `#637083`
- Divider: `#C9BDAE`, `#E8E1D7`
- Main accent: `#126C77`
- Secondary accent: `#B95B2E`
- Comparison accent: `#6E5AA7`
- Dark header/cover: `#10242B`

글꼴:

- 제목/큰 claim: `Noto Serif KR`
- 본문/카드 설명: `Noto Sans KR`
- 숫자/KPI/표 헤더: `Noto Sans KR Bold`
- 코드 블록: `Cascadia Code` 또는 Canva에서 가장 가까운 monospace font

텍스트 구성 규칙:

- 슬라이드 제목은 주제명이 아니라 결론형 claim으로 작성한다.
- 본문은 `소제목 + 짧은 설명 + 숫자/키워드 강조` 단위로 나눈다.
- 한 슬라이드에 긴 문단 하나만 두지 않는다.
- 카드 하나에는 메시지 하나만 넣는다.

표 디자인 규칙:

- 세로선 사용 금지
- 헤더 행은 `#10242B` 배경 + 흰색 텍스트
- 본문 행은 얇은 가로선만 사용
- 핵심 숫자는 굵게 + 청록/오렌지 포인트 컬러
- 최종 모델 행은 옅은 청록 배경으로 강조

이미지 정책:

- 이미지는 Canva에서 사용자가 직접 삽입한다.
- 각 슬라이드에는 이미지 placeholder와 삽입 파일 경로를 명시한다.

## 3. 필수 데이터

데이터:

- train: `40,000`
- test: `5,000`
- 정제 후 train: `39,272`
- 결측 본문: `8`
- 중복 본문: `637`
- 평균 길이: `546.05 → 524.48`
- 최대 길이: `32,767`
- 선택 어휘 수: `140,755`

실험 통제:

- seed: `42`
- train split: `27,490`
- valid split: `5,891`
- test split: `5,891`

모델 결과:

| model | macro F1 | elapsed |
|---|---:|---:|
| TF-IDF Random Forest | 0.7934 | 25.53s |
| LSTM | 0.7201 | 384.68s |
| Transformer (`klue/roberta-small`) | 0.8847 | 427.07s |

개선폭:

- best baseline 대비: `+0.0912`
- LSTM 대비: `+0.1646`

Transformer 설정:

- model: `klue/roberta-small`
- max_length: `160`
- batch_size: `32`
- epochs: `3`
- learning_rate: `2e-5`
- weight_decay: `0.01`
- device: `CUDA`

주요 오분류:

| true | predicted | count | ratio |
|---|---|---:|---:|
| 육아/교육 | 건강/복지 | 230 | 11.69% |
| 건강/복지 | 문화/예술/체육/언론 | 141 | 7.25% |
| 건강/복지 | 육아/교육 | 106 | 5.45% |

## 4. 슬라이드별 Canva 제작 스크립트

### 1. 표지

Claim:

국민청원 장문 텍스트를 전처리부터 Transformer까지 재현 가능한 파이프라인으로 분류했다.

구성:

- 좌측 60%: 대형 제목과 핵심 메시지
- 우측 40%: 프로젝트 구조 또는 청원 텍스트 예시 이미지 placeholder
- 하단: KPI 3개

텍스트:

- 제목: `국민청원 장문 텍스트 분류 NLP 프로젝트`
- 서브: `로컬 환경에서 데이터 정제, baseline, Transformer fine-tuning, 평가까지 End-to-End로 구현`
- KPI:
  - `0.8847` 최종 macro F1
  - `+0.0912` best baseline 대비
  - `5분` 핵심 발표 구성

이미지 placeholder:

- `README.md` 프로젝트 구조 캡처 또는 `data/raw/train.csv` 일부 캡처

### 2. 문제 정의

Claim:

국민청원 본문은 짧은 문장이 아니라 사회 이슈가 섞인 장문 분류 문제다.

구성:

- 좌측: 문제 정의 카드 3개
- 우측: 데이터 예시 캡처

카드:

1. 장문 텍스트
   - 평균 `546.05자`, 일부 본문 `32,767자`
2. 사회 이슈 중첩
   - 복지, 교육, 정책, 문화 이슈가 한 본문 안에서 함께 등장
3. 분류 목표
   - 건강/복지, 문화/예술/체육/언론, 육아/교육 3개 카테고리 자동 분류

우측 KPI:

- train `40,000`
- test `5,000`
- categories `3`

### 3. 데이터 품질과 EDA

Claim:

라벨은 균형적이지만 결측·중복·긴 본문이 모델링 리스크다.

구성:

- 좌측: 라벨 분포 mini bar 3개
- 중앙/하단: 리스크 카드 3개
- 우측: 고급 표 + 차트 placeholder

라벨 분포:

- 건강/복지 `13,301`
- 문화/예술/체육/언론 `13,337`
- 육아/교육 `13,362`

리스크 카드:

- 결측: train 본문 `8건`
- 중복: train 본문 `637건`
- 최대 길이: `32,767자`

이미지 placeholder:

- `reports/figures/category_distribution.svg`
- 또는 `reports/figures/text_length_distribution.svg`

### 4. 전처리 설계

Claim:

전처리는 단순 청소가 아니라 분류 신호를 남기고 청원 관용 표현을 줄이는 과정이다.

구성:

- 좌측: 코드 블록
- 우측: 전처리 단계 카드 4개

코드 블록:

```python
def normalize_text(value):
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[\w.+-]+@[\w-]+", " ", text)
    text = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()
```

카드:

- Noise 제거: HTML, URL, email 제거
- 본문 정규화: 특수문자와 공백 정리
- 학습 품질 관리: 결측·중복 본문 제거
- 도메인 불용어: 청원 관용 표현 제거

### 5. 전처리 결과와 파라미터 근거

Claim:

정제 후 39,272건으로 실험 데이터를 통제하고, 어휘 노이즈를 줄였다.

구성:

- 상단: KPI 3개
- 하단: 파라미터 카드 2개 + 이미지 placeholder

KPI:

- `40,000 → 39,272`: raw train → clean train
- `546.05 → 524.48`: 평균 길이 변화
- `140,755`: 선택 어휘 수

카드:

- `min_df=3`: 한두 문서에만 등장하는 오탈자·고유 잡음을 줄이면서 도메인 표현은 유지
- `max_df=0.85`: 너무 흔한 표현은 제거하되 사회 이슈 핵심어는 과도하게 버리지 않음

이미지 placeholder:

- `reports/figures/top_tokens_before_stopwords.svg`
- `reports/figures/top_tokens_after_stopwords.svg`

### 6. 실험 통제 구조

Claim:

모든 모델은 같은 split, 같은 seed, 같은 평가 지표로 비교했다.

구성:

- 좌측: 코드 카드
- 우측: split 표 + 공정성 체크 카드

코드:

```python
class SplitConfig:
    seed = 42
    train_ratio = 0.70
    valid_ratio = 0.15
    test_ratio = 0.15
```

표:

| split | rows | class balance |
|---|---:|---|
| train | 27,490 | 9,078 / 9,230 / 9,182 |
| valid | 5,891 | 1,945 / 1,978 / 1,968 |
| test | 5,891 | 1,945 / 1,978 / 1,968 |

공정성 카드:

- Seed: `42`
- Metric: F1 중심 평가
- Split: `70/15/15`

### 7. 모델 비교 설계

Claim:

빠른 baseline, 교재형 LSTM, 한국어 Transformer를 단계적으로 비교했다.

구성:

- 3단 모델 카드
- 카드 사이 화살표
- Transformer 카드 강조

카드:

1. TF-IDF Random Forest
   - 역할: 빠르고 안정적인 기준선
   - 한계: 문장 순서·문맥 반영 어려움
   - 결과: macro F1 `0.7934`

2. LSTM
   - 역할: 순서 정보 반영
   - 한계: `max_len=160`에서 긴 본문 손실
   - 결과: macro F1 `0.7201`

3. `klue/roberta-small`
   - 역할: 한국어 Transformer 실험군
   - 강점: subword + self-attention
   - 결과: macro F1 `0.8847`

### 8. Transformer 구현 코드

Claim:

DistilKoBERT 문제를 회피하고, 로컬 CUDA에서 안정적으로 학습 가능한 한국어 Transformer를 선택했다.

구성:

- 좌측: 의사결정 카드 2개
- 우측: 코드 블록
- 하단: 하이퍼파라미터 스트립

카드:

- 초기 후보: `monologg/distilkobert`, tokenizer loading 문제 발생
- 최종 선택: `klue/roberta-small`, Hugging Face에서 안정적으로 로딩

코드:

```python
tokenizer = AutoTokenizer.from_pretrained(config.model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    config.model_name,
    num_labels=len(LABELS),
)
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=2e-5,
    weight_decay=0.01,
)
```

하단 스트립:

- `max_length 160`
- `batch_size 32`
- `epochs 3`
- `lr 2e-5`
- `CUDA`

### 9. 최종 성능 결과

Claim:

Transformer는 macro F1 0.8847로 목표 0.88을 달성했다.

구성:

- 좌측: 성능 비교 차트 placeholder
- 우측: KPI 3개 + 고급 표

KPI:

- `0.8847`: Transformer macro F1
- `+0.0912`: best baseline 대비
- `+0.1646`: LSTM 대비

표:

| model | macro F1 | elapsed |
|---|---:|---:|
| TF-IDF RF | 0.7934 | 25.53s |
| LSTM | 0.7201 | 384.68s |
| Transformer | 0.8847 | 427.07s |

이미지 placeholder:

- `reports/figures/final_macro_f1_comparison.svg`

### 10. 오분류 분석

Claim:

남은 오류는 모델 성능 부족보다 사회정책 의미가 겹치는 라벨 경계 문제에 가깝다.

구성:

- 좌측: Confusion Matrix placeholder
- 우측: 오분류 패턴 카드 3개

카드:

1. 육아/교육 → 건강/복지
   - `230건`, `11.69%`
   - 아동, 돌봄, 복지 이슈 중첩

2. 건강/복지 → 문화/언론
   - `141건`, `7.25%`
   - 공공 캠페인, 체육·복지 연결

3. 건강/복지 → 육아/교육
   - `106건`, `5.45%`
   - 보호, 제도 개선, 교육복지 혼합

이미지 placeholder:

- `reports/figures/kobert_confusion_matrix.svg`

### 11. 결론과 후속 개선

Claim:

목표 성능은 달성했지만 긴 본문 truncation과 라벨 경계 혼동은 다음 개선 과제다.

구성:

- 좌측: 성과 카드 3개
- 우측: 개선 로드맵 4단계

성과 카드:

- 환경: Miniconda / PyTorch CUDA 로컬 재현 환경
- 파이프라인: EDA → 전처리 → baseline → Transformer → 평가
- 성능: macro F1 `0.8847`, 목표 `0.88` 달성

로드맵:

1. 문단 단위 예측 앙상블
2. `max_length 256/512` 실험
3. KLUE-RoBERTa-base / KoELECTRA 비교
4. 계층형 또는 multi-label 검토

마무리 문장:

> 핵심은 높은 점수 하나가 아니라, 왜 그 결과가 나왔는지 코드와 수치로 설명 가능한 구조를 만든 것이다.

## 5. Canva 작업 체크리스트

- [ ] 16:9 프레젠테이션으로 생성
- [ ] Data Focus 계열 템플릿 또는 유사한 clean analytics 템플릿 선택
- [ ] 모든 슬라이드 제목을 claim 문장으로 작성
- [ ] 긴 줄글을 카드 단위로 분리
- [ ] 표는 세로선 없이 modern table로 디자인
- [ ] 최종 모델 숫자 `0.8847`, `+0.0912`, `+0.1646` 강조
- [ ] 코드 슬라이드 4, 6, 8 포함
- [ ] 이미지 placeholder에 지정 파일 경로 표시
- [ ] 발표자가 대본 없이 설명할 수 있도록 각 슬라이드의 근거 구조 유지
