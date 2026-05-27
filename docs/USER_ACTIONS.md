# 사용자 외부 조치 목록

## 완료된 필수 조치

### 1. 노출된 GitHub Personal Access Token 폐기

학교 제출용 HWP 문서에 GitHub Personal Access Token으로 보이는 값이 포함되어 있었다. 저장소에서는 해당 HWP 파일을 `.gitignore`로 제외했지만, 이미 문서에 기록된 토큰은 계정 보안을 위해 반드시 폐기해야 한다.

- 상태: 2026-05-27 사용자 확인 기준 폐기 완료
- 새 토큰이 필요하면 최소 권한과 짧은 만료 기간으로 다시 만든다.
- 새 토큰은 HWP, README, PLAN, 코드, 커밋 메시지에 기록하지 않는다.

## 선택

### 2. Anaconda Prompt에서 학습 환경 생성

현재 PowerShell PATH에서는 `conda` 명령이 감지되지 않았다. Anaconda가 설치되어 있다면 Anaconda Prompt를 열어 아래 환경을 만든다.

```bash
conda create -n nlp-petition python=3.10
conda activate nlp-petition
pip install -r requirements.txt
```

PyTorch GPU 버전은 CUDA 호환성에 따라 공식 설치 명령이 달라질 수 있으므로, 실제 모델 학습 직전에 PyTorch 공식 설치 페이지 기준으로 확정한다.
