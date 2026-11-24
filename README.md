# NLP 프로젝트 작업 공간

프로젝트별 작업은 각각의 하위 폴더에서 진행합니다.

- [petition-classification/](petition-classification/): 기존 국민청원 장문 텍스트 분류 프로젝트
- [gb-electricity-lstm/](gb-electricity-lstm/): 영국 전력수요 예측 딥러닝 과제(NESO 2022~2025년 자료)
- [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md): 공통 구조와 관리 원칙
- [SECURITY_CHECK.md](SECURITY_CHECK.md): 공통 보안 기준과 기존 점검 기록
- `.claude/skills/`: 공통 작업 스킬
- `.gitignore`: 모든 프로젝트에 적용하는 Git 제외 규칙

새 프로젝트는 이 디렉터리에 별도의 하위 폴더를 만들어 진행합니다. 프로젝트별 코드, 데이터, 의존성, 계획서, 보고서와 제출물은 해당 프로젝트 폴더 안에 두고, 공통 문서는 상위에 둡니다.

## 기존 프로젝트 실행

```powershell
cd petition-classification
pip install -r requirements.txt
python src/preprocess.py
```

상세 설명은 [기존 프로젝트 README](petition-classification/README.md)를 참고하세요. 각 프로젝트는 별도 가상 환경에서 의존성을 관리합니다.
