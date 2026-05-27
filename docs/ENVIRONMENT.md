# 로컬 환경 구성 메모

## 목표

국민청원 데이터 수집, 전처리, 모델 학습, 평가를 Colab이 아니라 로컬 Anaconda 환경에서 재현할 수 있도록 구성한다.

## 권장 환경

- OS: Windows
- Shell: Anaconda Prompt 또는 PowerShell
- Python: 3.10
- Environment name: `nlp-petition`
- Main framework: PyTorch
- Transformer library: Hugging Face `transformers`

## 기본 설치 명령

```bash
conda create -n nlp-petition python=3.10
conda activate nlp-petition
pip install pandas numpy scikit-learn matplotlib seaborn
pip install torch transformers sentencepiece
```

## KoBERT 설치 방침

KoBERT는 프로젝트 구현 시점에 유지보수 상태가 좋은 방식을 선택한다.

- 1순위: Hugging Face에서 바로 로드 가능한 한국어 BERT 계열 모델
- 2순위: 공식 또는 널리 사용되는 KoBERT 호환 패키지

선택한 모델명, 설치 명령, 버전은 결과 보고서와 실험 로그에 반드시 기록한다.

## 재현성 기준

- 모든 실험은 동일한 seed를 사용한다.
- 데이터 분할은 베이스라인과 KoBERT가 같은 split을 공유한다.
- 패키지 버전은 최종 제출 전 `pip freeze > requirements.txt`로 고정한다.
- GPU를 사용한 경우 CUDA, PyTorch, GPU 모델명을 기록한다.
