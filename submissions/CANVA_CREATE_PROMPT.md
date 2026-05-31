# Canva 생성 프롬프트

아래 내용을 Canva의 프레젠테이션 생성/Canva Docs/Magic Design 프롬프트에 입력한다.

---

16:9 한국어 최종 발표 프레젠테이션을 만들어 주세요. 주제는 "국민청원 장문 텍스트 분류 NLP 프로젝트"입니다. 스타일은 Data Focus 계열의 clean analytics deck으로, 데이터와 코드 근거가 돋보이도록 디자인해 주세요.

디자인 조건:

- 배경은 따뜻한 오프화이트 `#F7F4EE`, 메인 텍스트는 딥잉크 `#17212B`.
- 포인트 컬러는 청록 `#126C77`, 오렌지브라운 `#B95B2E`, 보라 `#6E5AA7`.
- 제목은 결론형 claim 문장으로 작성하고, 본문은 긴 줄글이 아니라 `소제목 + 짧은 설명 + 강조 숫자` 카드로 나누어 주세요.
- 표는 기본 검은 테두리 표를 쓰지 말고, 헤더 배경색, 얇은 가로선, 세로선 없음, 핵심 숫자 볼드/포인트 컬러로 디자인해 주세요.
- 코드가 들어가는 슬라이드는 어두운 코드 패널을 사용하고 monospace 글꼴로 표현해 주세요.
- 이미지는 실제로 넣지 말고, 각 위치에 "이미지/캡처 삽입 위치" placeholder와 삽입할 파일 경로를 표시해 주세요.

발표 목적:

교수님 요구사항을 반영해야 합니다. 발표자는 대본을 읽는 것이 아니라, 코드 흐름, 전처리 근거, 파라미터 선택 이유, 모델 선택 이유, 성능 결과, Confusion Matrix 기반 오분류 분석을 직접 설명할 수 있어야 합니다.

핵심 수치:

- train 40,000건, test 5,000건
- 정제 후 train 39,272건
- 결측 본문 8건, 중복 본문 637건
- 평균 길이 546.05 → 524.48
- 최대 길이 32,767자
- 선택 어휘 수 140,755
- seed 42
- split: train 27,490 / valid 5,891 / test 5,891
- TF-IDF Random Forest macro F1 0.7934
- LSTM macro F1 0.7201
- Transformer `klue/roberta-small` macro F1 0.8847
- best baseline 대비 +0.0912, LSTM 대비 +0.1646
- Transformer 설정: max_length 160, batch_size 32, epochs 3, learning_rate 2e-5, weight_decay 0.01, CUDA

슬라이드 구성은 11장입니다.

1. 표지  
Claim: 국민청원 장문 텍스트를 전처리부터 Transformer까지 재현 가능한 파이프라인으로 분류했다.  
KPI: 0.8847 최종 macro F1, +0.0912 best baseline 대비, 5분 핵심 발표 구성.  
Placeholder: README.md 프로젝트 구조 캡처 또는 data/raw/train.csv 일부 캡처.

2. 문제 정의  
Claim: 국민청원 본문은 짧은 문장이 아니라 사회 이슈가 섞인 장문 분류 문제다.  
카드: 장문 텍스트, 사회 이슈 중첩, 분류 목표.  
KPI: train 40,000 / test 5,000 / categories 3.

3. 데이터 품질과 EDA  
Claim: 라벨은 균형적이지만 결측·중복·긴 본문이 모델링 리스크다.  
라벨 분포: 건강/복지 13,301, 문화/예술/체육/언론 13,337, 육아/교육 13,362.  
리스크: 결측 8, 중복 637, 최대 길이 32,767.  
Placeholder: reports/figures/category_distribution.svg 또는 reports/figures/text_length_distribution.svg.

4. 전처리 설계  
Claim: 전처리는 단순 청소가 아니라 분류 신호를 남기고 청원 관용 표현을 줄이는 과정이다.  
좌측에는 `src/preprocess.py`의 `normalize_text` 코드 블록.  
우측 카드: Noise 제거, 본문 정규화, 학습 품질 관리, 도메인 불용어.

5. 전처리 결과와 파라미터 근거  
Claim: 정제 후 39,272건으로 실험 데이터를 통제하고, 어휘 노이즈를 줄였다.  
KPI: 40,000 → 39,272, 546.05 → 524.48, 140,755.  
카드: min_df=3, max_df=0.85 선택 이유.  
Placeholder: reports/figures/top_tokens_before_stopwords.svg + reports/figures/top_tokens_after_stopwords.svg.

6. 실험 통제 구조  
Claim: 모든 모델은 같은 split, 같은 seed, 같은 평가 지표로 비교했다.  
코드: SplitConfig seed=42, train 0.70, valid 0.15, test 0.15.  
표: train 27,490 / valid 5,891 / test 5,891.  
카드: Seed 42, Metric F1, Split 70/15/15.

7. 모델 비교 설계  
Claim: 빠른 baseline, 교재형 LSTM, 한국어 Transformer를 단계적으로 비교했다.  
3단 카드: TF-IDF Random Forest, LSTM, klue/roberta-small.  
Transformer 카드를 가장 강조.

8. Transformer 구현 코드  
Claim: DistilKoBERT 문제를 회피하고, 로컬 CUDA에서 안정적으로 학습 가능한 한국어 Transformer를 선택했다.  
카드: 초기 후보 monologg/distilkobert tokenizer 문제, 최종 선택 klue/roberta-small.  
코드: AutoTokenizer, AutoModelForSequenceClassification, AdamW.  
하단 스트립: max_length 160, batch_size 32, epochs 3, lr 2e-5, CUDA.

9. 최종 성능 결과  
Claim: Transformer는 macro F1 0.8847로 목표 0.88을 달성했다.  
KPI: 0.8847, +0.0912, +0.1646.  
표: TF-IDF RF 0.7934, LSTM 0.7201, Transformer 0.8847.  
Placeholder: reports/figures/final_macro_f1_comparison.svg.

10. 오분류 분석  
Claim: 남은 오류는 모델 성능 부족보다 사회정책 의미가 겹치는 라벨 경계 문제에 가깝다.  
카드: 육아/교육→건강/복지 230건 11.69%, 건강/복지→문화/언론 141건 7.25%, 건강/복지→육아/교육 106건 5.45%.  
Placeholder: reports/figures/kobert_confusion_matrix.svg.

11. 결론과 후속 개선  
Claim: 목표 성능은 달성했지만 긴 본문 truncation과 라벨 경계 혼동은 다음 개선 과제다.  
성과 카드: 환경, 파이프라인, 성능.  
로드맵: 문단 단위 예측 앙상블, max_length 256/512 실험, KLUE-RoBERTa-base/KoELECTRA 비교, 계층형 또는 multi-label 검토.  
마무리 문장: 핵심은 높은 점수 하나가 아니라, 왜 그 결과가 나왔는지 코드와 수치로 설명 가능한 구조를 만든 것이다.

---
