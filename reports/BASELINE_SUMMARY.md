# 베이스라인 모델 학습 결과

## 1. 목적

KoBERT 파인튜닝 전 비교 기준을 만들기 위해 동일한 데이터 분할에서 TF-IDF 기반 Random Forest와 교재 수준의 LSTM 모델을 학습했다.

## 2. 데이터 분할

- Seed: `42`
- Split: train 70%, validation 15%, test 15%
- Stratified split 기준: `category`
- KoBERT 단계에서도 같은 `data/processed/split_indices.csv`를 사용한다.

| split | rows | 0_인권/성평등 | 1_문화/예술/체육/언론 | 2_육아/교육 |
| --- | --- | --- | --- | --- |
| train | 27490 | 9078 | 9230 | 9182 |
| valid | 5891 | 1945 | 1978 | 1968 |
| test | 5891 | 1945 | 1978 | 1968 |

## 3. 모델별 성능

| model | accuracy | macro precision | macro recall | macro F1 | weighted F1 | elapsed seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| tfidf_random_forest | 0.7934 | 0.7939 | 0.7933 | 0.7934 | 0.7936 | 25.53 |
| lstm | 0.7225 | 0.7213 | 0.7219 | 0.7201 | 0.7205 | 384.68 |

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
