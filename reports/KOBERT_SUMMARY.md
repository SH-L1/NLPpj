# KoBERT 호환 한국어 Transformer 파인튜닝 결과

## 1. 모델 선택

- 1차 후보: `monologg/distilkobert`
- 실제 사용 모델: `klue/roberta-small`
- 선택 사유: `monologg/distilkobert`는 현재 Transformers 5.9 환경에서 tokenizer 로딩이 실패했다. `klue/roberta-small`은 Hugging Face에서 바로 로딩 가능한 경량 한국어 Transformer이며, 로컬 CUDA 환경에서 전체 split 재학습이 가능한 KoBERT 호환 실험군으로 사용했다.

## 2. 학습 설정

- Seed: `42`
- Max length: `160`
- Batch size: `32`
- Epochs: `3`
- Learning rate: `2e-05`
- Weight decay: `0.01`
- Device: `cuda`
- Train samples: `27,490` from baseline train split
- Validation samples: `5,891` from baseline validation split
- Test samples: `5,891` from baseline test split
- Gradient accumulation: `1`

전체 baseline split을 사용했다.

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
| kobert_compatible_klue_roberta_small | 0.8847 | 0.8859 | 0.8846 | 0.8847 | 0.8848 |

## 5. 베이스라인 대비

- 가장 높은 베이스라인 macro F1: `tfidf_random_forest` = `0.7934`
- Transformer macro F1: `0.8847`
- 차이: `+0.0912`

이번 결과는 GPU 환경에서 전체 train split, 더 긴 epoch, 더 큰 max length로 재학습한 결과다. 베이스라인 대비 성능 개선 여부를 최종 비교 근거로 사용한다.

## 6. 산출물

- `src/train_kobert.py`
- `reports/outputs/kobert_metrics.csv`
- `reports/outputs/kobert_classification_report.csv`
- `reports/outputs/kobert_confusion_matrix.csv`
- `logs/kobert_training_log.csv`
- `models/kobert_compatible_classifier.pt`
