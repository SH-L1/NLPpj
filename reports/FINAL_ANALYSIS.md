# 최종 성능 비교 및 결과 해석

## 1. 모델별 최종 성능

| model | accuracy | macro_precision | macro_recall | macro_f1 | weighted_f1 | elapsed_seconds |
| --- | --- | --- | --- | --- | --- | --- |
| kobert_compatible_klue_roberta_small | 0.8847 | 0.8859 | 0.8846 | 0.8847 | 0.8848 | 427.0700 |
| tfidf_random_forest | 0.7934 | 0.7939 | 0.7933 | 0.7934 | 0.7936 | 25.5300 |
| lstm | 0.7225 | 0.7213 | 0.7219 | 0.7201 | 0.7205 | 384.6800 |

- 최고 베이스라인: `tfidf_random_forest` macro F1 `0.7934`
- Transformer 계열 모델: `klue/roberta-small` macro F1 `0.8847`
- 최고 베이스라인 대비 개선폭: `+0.0912`
- LSTM 대비 개선폭: `+0.1646`
- 목표 F1 0.88 달성 여부: `True`

성능 변화 차트는 `reports/figures/final_macro_f1_comparison.svg`에 저장했다.

## 2. Confusion Matrix 기반 오분류 분석

카테고리별 recall:

| model | label_id | label | support | correct | wrong | recall |
| --- | --- | --- | --- | --- | --- | --- |
| tfidf_random_forest | 0 | 인권/성평등 | 1945 | 1490 | 455 | 0.7661 |
| tfidf_random_forest | 1 | 문화/예술/체육/언론 | 1978 | 1617 | 361 | 0.8175 |
| tfidf_random_forest | 2 | 육아/교육 | 1968 | 1567 | 401 | 0.7962 |
| lstm | 0 | 인권/성평등 | 1945 | 1177 | 768 | 0.6051 |
| lstm | 1 | 문화/예술/체육/언론 | 1978 | 1577 | 401 | 0.7973 |
| lstm | 2 | 육아/교육 | 1968 | 1502 | 466 | 0.7632 |
| kobert_compatible_klue_roberta_small | 0 | 인권/성평등 | 1945 | 1698 | 247 | 0.8730 |
| kobert_compatible_klue_roberta_small | 1 | 문화/예술/체육/언론 | 1978 | 1832 | 146 | 0.9262 |
| kobert_compatible_klue_roberta_small | 2 | 육아/교육 | 1968 | 1682 | 286 | 0.8547 |

Transformer 모델의 주요 오분류:

| true_label | predicted_label | count | ratio_in_true_label |
| --- | --- | --- | --- |
| 육아/교육 | 인권/성평등 | 230 | 0.1169 |
| 인권/성평등 | 문화/예술/체육/언론 | 141 | 0.0725 |
| 인권/성평등 | 육아/교육 | 106 | 0.0545 |

해석:

- `인권/성평등`과 `육아/교육` 사이의 오분류가 가장 크다. 두 카테고리는 학교, 아동, 보호, 제도 개선처럼 사회정책 어휘를 공유하기 때문이다.
- `문화/예술/체육/언론`은 Transformer 모델에서 recall이 가장 높다. 체육협회, 언론, 문화예술 등 고유 도메인 어휘가 비교적 명확하기 때문이다.
- RandomForest는 빠르고 안정적인 baseline이지만 문장 순서와 문맥을 반영하지 못한다.
- LSTM은 순차 모델이지만 `max_len=160` 제한과 단어 단위 토큰화 때문에 긴 청원 본문 전체 맥락을 충분히 반영하지 못했다.

## 3. 전처리 및 파라미터 효과

전처리 전후 비교:

| stage | rows | mean_length | median_length | vocabulary_size |
| --- | --- | --- | --- | --- |
| raw_tokenized | 40000 | 546.0478 | 313.0000 | 735792 |
| cleaned_stopwords_removed | 39272 | 524.4797 | 303.0000 | 735749 |

선택한 TF-IDF 어휘 파라미터:

- `min_df=3`
- `max_df=0.85`
- 선택 어휘 수: `140,755`

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
- 실제 결과에서도 macro F1이 최고 baseline 대비 `+0.0912` 개선되었다.

## 5. 한계와 후속 개선

- `monologg/distilkobert`는 tokenizer 호환 문제로 직접 사용하지 못했고, `klue/roberta-small`로 대체했다.
- max length 160을 넘는 긴 본문은 여전히 일부 잘린다.
- 국민청원 라벨은 사회 이슈가 겹치는 경우가 많아 `인권/성평등`과 `육아/교육` 사이 혼동이 남아 있다.
- 다음 단계에서는 긴 본문을 문단 단위로 나누어 예측을 앙상블하거나, 더 큰 한국어 사전학습 모델을 비교할 수 있다.
