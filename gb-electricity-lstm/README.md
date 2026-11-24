# 소형 LSTM을 활용한 영국 전력수요 예측

Great Britain(잉글랜드·스코틀랜드·웨일스)의 과거 전력수요로 다음 30분의 National Demand를 예측하는 딥러닝 과제입니다. 수업 수준에서 설명할 수 있는 소형 LSTM을 사용하며, 기준모델과 비교해 오류 원인과 개선 과정을 기록합니다.

## 현재 단계: 전처리 및 탐색적 데이터 분석 완료

- 관측 기간: 2022-01-01 ~ 2025-12-31
- 공급자: National Energy System Operator(NESO)
- 원본: `data/raw/demanddata_2022.csv` ~ `demanddata_2025.csv`
- 전체: 70,128행, 30분 단위
- 시간순 분리: 2022~2023년 학습 35,040행, 2024년 검증 17,568행, 2025년 최종 평가 17,520행
- EDA는 학습 기간에 한정했습니다. 모델 학습과 검증·최종 평가는 다음 단계입니다.

자세한 출처, 수집 결과, 날짜·컬럼 차이는 [데이터 수집 기록](docs/DATA_COLLECTION.md)을 참고하세요.

현재 단계의 [중간 보고서 PDF](output/pdf/gb_electricity_collection_report.pdf)와 [편집용 본문](output/pdf/gb_electricity_collection_report.txt)을 제공합니다. 제공된 보고서 양식에 맞춰 8쪽으로 구성했으며, 미수행 항목은 계획으로 구분했습니다. `python scripts/make_collection_report.py`로 다시 생성할 수 있습니다(ReportLab 및 Windows 맑은 고딕 필요).

## 재현 방법

Python 3.10 이상, 표준 라이브러리만 사용합니다. 이 단계에서는 별도 패키지가 필요하지 않습니다.

```powershell
cd gb-electricity-lstm
python scripts/collect_data.py
```

네트워크 연결과 NESO 공개 서버 접근이 필요합니다. 원본 CSV가 이미 있으면 덮어쓰지 않고 종료합니다. 다운로드 중단 후에는 `--resume`을 사용합니다. 기존 CSV가 서버의 현재 내용과 다르면 보존하고 오류로 중단합니다.

```powershell
python scripts/collect_data.py --offline
```

오프라인 검증은 파일 해시, 관측 기간, 필수 컬럼, 결측, 중복, 서머타임 구간 수를 재확인합니다. 수집 기록과 검증 결과는 `data/metadata/`에 보관합니다. 원본 CSV는 공통 `.gitignore`에 따라 커밋하지 않고 재현 코드와 출처 기록을 커밋합니다.

## 전처리와 EDA 재현

프로젝트 폴더에서 실행합니다.

```powershell
python -m pip install -r requirements-eda.txt
python scripts/preprocess.py
python scripts/analyze_demand.py
```

전처리는 연도별 원본을 확인하고, 영국 현지 정산일과 구간 번호를 연속된 UTC 시각으로 변환합니다. `data/processed/`의 학습·검증·평가 CSV는 재생성하며, 원본과 함께 Git에서 제외합니다. 모델 학습에 사용할 표준화는 학습 시점에 수행합니다.

- [전처리 검증 결과](reports/outputs/preprocessing_audit.json)
- [EDA 요약 통계](reports/outputs/eda_summary.json), [일중 패턴](reports/outputs/eda_daily_profiles.csv), [월별 평균](reports/outputs/eda_monthly.csv), [시차 관계](reports/outputs/eda_lags.csv)
- [수요 분포](reports/figures/nd_distribution.svg), [평일·주말 일중 패턴](reports/figures/nd_daily_profiles.svg), [월별 평균](reports/figures/nd_monthly.svg), [과거 수요와의 관계](reports/figures/nd_lag_relationship.svg)

## 보고서 작성 기준

- 제공된 최종 보고서 양식을 따르고 약 15쪽으로 구성합니다.
- 분석 질문에 답하고, 모델 선택 이유와 지표의 의미를 설명합니다.
- 초기 실험 → 관측된 문제 → 원인 가설과 근거 → 변경 사항 → 개선 여부를 기록합니다.
- 실제로 수행한 실험과 계산된 평가값만 기재합니다. 실패하거나 개선되지 않은 실험도 남깁니다.
- 차트와 오류 사례를 포함하고, 테스트 성능을 보면서 반복 조정하지 않습니다.
- 새 프로젝트의 커밋은 `deeplearning` 브랜치에서 사용자의 Git 계정으로 진행합니다.
