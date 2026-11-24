# 저장소 구조

```text
NLPpj/
├── README.md                    # 전체 작업 공간 안내
├── REPOSITORY_STRUCTURE.md      # 공통 구조와 관리 원칙
├── SECURITY_CHECK.md            # 공통 보안 기준 및 점검 기록
├── .gitignore                   # 모든 프로젝트에 적용하는 제외 규칙
├── .claude/skills/              # 공통 작업 스킬
├── gb-electricity-lstm/         # 영국 전력수요 예측 딥러닝 과제
│   ├── README.md
│   ├── data/raw/               # 수집한 원본 CSV, Git 제외
│   ├── data/metadata/          # 출처, 파일 해시, 수집 검증 기록
│   ├── docs/                  # 프로젝트 전용 문서
│   └── scripts/               # 데이터 수집 및 검증 코드
└── petition-classification/     # 기존 국민청원 분류 프로젝트
    ├── README.md
    ├── PLAN.md
    ├── requirements.txt
    ├── configs/
    ├── data/raw/
    ├── data/processed/
    ├── docs/                    # 데이터 출처, 실행 환경, 사용자 조치 기록
    ├── logs/
    ├── models/
    ├── notebooks/
    ├── reports/figures/
    ├── reports/outputs/
    ├── scripts/
    ├── src/
    └── submissions/
```

두 프로젝트는 같은 깊이의 독립된 폴더에서 관리합니다. 새 딥러닝 과제는 `gb-electricity-lstm/`에서 진행하며 `deeplearning` 브랜치에 커밋합니다.

## 관리 원칙

- 공통 문서와 저장소 설정은 최상위에 둡니다.
- 프로젝트별 코드, 데이터, 환경 설정, 계획서, 실험 결과와 제출물은 각 프로젝트 안에 둡니다.
- 실행 명령과 프로젝트 문서 속 상대 경로는 해당 프로젝트 폴더를 기준으로 합니다.
- 프로젝트마다 별도의 가상 환경과 의존성 파일을 사용합니다.
- Git 저장소는 최상위의 `.git/` 하나로 함께 관리합니다.
- 원본 데이터와 모델 체크포인트, 개인정보가 포함될 수 있는 제출 문서는 Git에서 제외합니다.
- 보고서용 최종 표와 그림은 검토 후 선별적으로 커밋합니다.
