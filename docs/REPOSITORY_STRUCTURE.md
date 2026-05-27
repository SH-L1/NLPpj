# 저장소 구조 설계

```text
NLPpj/
├── README.md
├── PLAN.md
├── .gitignore
├── data/
│   ├── raw/                 # 원본 데이터 보관 위치, Git 커밋 제외
│   └── processed/           # 정제 데이터 보관 위치, Git 커밋 제외
├── docs/
│   ├── ENVIRONMENT.md       # 로컬 환경 구성 메모
│   ├── REPOSITORY_STRUCTURE.md
│   └── SECURITY_CHECK.md    # 보안 점검 기록
├── logs/                    # 실험 로그, Git 커밋 제외
├── models/                  # 모델 체크포인트, Git 커밋 제외
├── notebooks/               # EDA와 실험 노트북
├── reports/
│   ├── figures/             # 보고서용 그림, 필요 시 선별 커밋
│   └── outputs/             # 성능표와 분석 결과, 필요 시 선별 커밋
├── src/                     # 전처리, 학습, 평가 코드
└── submissions/             # 학교 제출용 원본 문서, Git 커밋 제외
```

## 관리 원칙

- 원본 데이터와 모델 체크포인트는 파일 크기와 라이선스 문제를 피하기 위해 Git에 커밋하지 않는다.
- 학교 제출용 HWP 파일은 개인정보와 인증 정보가 포함될 수 있으므로 Git에 커밋하지 않는다.
- 실험 결과 중 보고서에 들어갈 최종 표와 그림만 검토 후 선별적으로 커밋한다.
- 코드는 `src/`, 분석 노트북은 `notebooks/`, 문서는 `docs/`와 `reports/`에 분리한다.
