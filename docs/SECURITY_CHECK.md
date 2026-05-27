# 보안 점검 기록

## 현재 확인 사항

- 학교 제출용 HWP 문서에는 개인정보 또는 인증 정보가 포함될 수 있다.
- 특히 GitHub Personal Access Token으로 보이는 문자열이 포함된 문서는 공개 저장소에 올리면 안 된다.
- `submissions/*.hwp`, `submissions/*.hwpx`, `submissions/*.docx`, `submissions/*.pdf`는 `.gitignore`로 커밋 제외 처리했다.
- `data/raw/`, `data/processed/`, `models/`, `logs/`의 생성물도 기본적으로 커밋 제외 처리했다.

## 2026-05-27 점검 결과

- `data/raw/train.csv`, `data/raw/test.csv`는 Git ignored 상태로 확인했다.
- `submissions/*.hwp`는 Git ignored 상태로 확인했다.
- 공개 후보 파일에서 `github_pat`, `ghp_`, 전화번호 패턴, 학교 이메일 패턴을 검색했으며 실제 민감 정보는 발견되지 않았다.
- 저장소 차원의 차단은 완료했다.
- HWP 문서에 노출됐던 GitHub Personal Access Token은 2026-05-27 사용자 확인 기준으로 폐기 완료했다.

## 즉시 해야 할 일

- [x] 노출된 GitHub Personal Access Token을 GitHub에서 폐기한다. 2026-05-27 사용자 확인 기준 완료.
- [ ] 새 토큰이 필요하면 최소 권한과 짧은 만료 기간으로 재발급한다.
- [ ] 제출용 문서에서 토큰, 전화번호, 생년월일, 이메일 등 공개 불필요 정보를 제거한 별도 공개본을 만든다.
- [ ] 공개 저장소에 올릴 문서에는 실제 토큰 문자열을 절대 기록하지 않는다.

## 커밋 전 점검 명령

```bash
git status --short
git diff --check
```

민감 정보 의심 패턴은 커밋 전에 추가로 검색한다.

```bash
rg "github_pat|ghp_|token|password|010-|@sunmoon|생년월일|연락처"
```

## 공개 가능 기준

- 실제 인증 토큰 문자열이 없다.
- 전화번호, 생년월일, 개인 이메일 등 개인정보가 없다.
- 원본 데이터와 모델 체크포인트가 없다.
- 문서에 포함된 AI 활용 내역은 문제 해결 과정과 최종 판단을 구분해 기록한다.
