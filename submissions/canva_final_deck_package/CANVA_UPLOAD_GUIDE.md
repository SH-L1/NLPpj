# Canva 업로드 실행 가이드

현재 세션에는 Canva 생성/편집 API 도구가 노출되지 않는다. 대신 Canva에서 바로 이어서 작업할 수 있도록 업로드용 패키지를 준비했다.

## 1. Canva에 업로드할 파일

먼저 아래 PPTX를 Canva에 업로드한다.

`submissions/canva_assets/canva_upload_국민청원_장문텍스트_분류_최종발표.pptx`

Canva에서:

1. Canva 열기
2. `디자인 만들기` → `프레젠테이션 16:9`
3. `업로드` → 위 PPTX 업로드
4. 업로드된 PPTX를 Canva 디자인으로 열기
5. 글꼴/간격이 깨진 슬라이드는 `CANVA_FINAL_DECK_BRIEF.md` 기준으로 보정

## 2. Canva 생성형 기능을 사용할 경우

Canva의 Magic Design, Canva Docs, 또는 프레젠테이션 생성 프롬프트에는 아래 파일 내용을 붙여 넣는다.

`submissions/CANVA_CREATE_PROMPT.md`

생성 후에는 아래 파일을 기준으로 슬라이드별 내용과 수치를 검수한다.

`submissions/CANVA_FINAL_DECK_BRIEF.md`

## 3. 삽입용 차트 이미지

Canva에는 SVG보다 PNG가 안정적으로 들어가는 경우가 많으므로 PNG를 우선 사용한다.

| slide | recommended PNG |
|---:|---|
| 3 | `submissions/canva_assets/category_distribution.png` |
| 3 | `submissions/canva_assets/text_length_distribution.png` |
| 5 | `submissions/canva_assets/top_tokens_before_stopwords.png` |
| 5 | `submissions/canva_assets/top_tokens_after_stopwords.png` |
| 9 | `submissions/canva_assets/final_macro_f1_comparison.png` |
| 10 | `submissions/canva_assets/kobert_confusion_matrix.png` |

SVG 원본도 같은 폴더에 함께 보관되어 있다.

## 4. 최종 검수 기준

- 슬라이드 수: 11장
- 모든 슬라이드 제목은 claim 문장
- 긴 줄글 대신 카드형/다단형 모듈 사용
- 표는 세로선 없이 헤더 배경 + 얇은 가로선
- 코드 슬라이드 4, 6, 8 포함
- `0.8847`, `+0.0912`, `+0.1646` 강조
- `min_df=3`, `max_df=0.85`, `seed=42`, `max_length=160`, `batch_size=32`, `learning_rate=2e-5` 포함
- 교수님 요구사항인 코드 흐름, 파라미터 선택 이유, 모델 선택 이유, 오분류 분석 설명 가능
