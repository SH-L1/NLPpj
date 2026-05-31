# Canva 최종 발표 덱 패키지 README

이 패키지는 Canva에서 `국민청원 장문 텍스트 분류 NLP 프로젝트` 최종 발표 덱을 처음부터 다시 만들거나, 업로드용 PPTX를 기반으로 Canva에서 편집하기 위한 파일 묶음이다.

## 가장 빠른 사용 방법

1. Canva에서 새 16:9 프레젠테이션을 만든다.
2. `canva_assets/canva_upload_국민청원_장문텍스트_분류_최종발표.pptx`를 업로드한다.
3. Canva에서 PPTX를 연 뒤, 폰트/간격이 어긋난 슬라이드를 `CANVA_FINAL_DECK_BRIEF.md` 기준으로 보정한다.
4. 차트 placeholder에는 `canva_assets/*.png` 파일을 우선 삽입한다.
5. 최종 검수는 `CANVA_UPLOAD_GUIDE.md`의 체크리스트로 한다.

## 생성형 Canva 기능을 쓸 때

Canva Magic Design, Canva Docs, 또는 프레젠테이션 생성 프롬프트를 쓸 경우:

1. `CANVA_CREATE_PROMPT.md` 내용을 그대로 붙여 넣는다.
2. 생성 결과를 `CANVA_FINAL_DECK_BRIEF.md`와 대조한다.
3. 표, 코드, KPI, 오분류 분석이 누락되면 수동으로 보완한다.

## 파일 설명

| file/folder | purpose |
|---|---|
| `canva_assets/` | Canva 업로드용 PPTX, PNG 차트, SVG 원본 |
| `CANVA_CREATE_PROMPT.md` | Canva 생성형 기능에 붙여 넣을 프롬프트 |
| `CANVA_FINAL_DECK_BRIEF.md` | 전체 디자인/내용/슬라이드별 제작 명세 |
| `CANVA_ASSET_MANIFEST.md` | 슬라이드별 삽입 에셋 목록 |
| `CANVA_UPLOAD_GUIDE.md` | Canva 업로드 및 최종 검수 절차 |

## 반드시 유지할 발표 요구사항

- 11장 구성
- Data Focus 스타일
- 긴 줄글 대신 카드형/다단형 정보 모듈
- 기본 검은 테두리 표 금지
- 코드 슬라이드 4, 6, 8 포함
- 교수님 질문 대비: 코드 흐름, 전처리 근거, 파라미터 선택 이유, 모델 선택 이유, 성능 결과, 오분류 분석 설명 가능

## 반드시 포함할 핵심 수치

- 최종 Transformer macro F1: `0.8847`
- best baseline 대비: `+0.0912`
- LSTM 대비: `+0.1646`
- `min_df=3`
- `max_df=0.85`
- `seed=42`
- `max_length=160`
- `batch_size=32`
- `learning_rate=2e-5`
