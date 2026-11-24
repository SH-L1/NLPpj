"""Build the collection-stage report from audited evidence; no model results are generated."""
import json
import platform
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab import Version
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing, String, Rect, Line

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
AUDIT = json.loads((ROOT / 'data/metadata/collection_audit.json').read_text(encoding='utf-8'))
MANIFEST = json.loads((ROOT / 'data/metadata/download_manifest.json').read_text(encoding='utf-8'))
assert AUDIT['all_checks_passed'] and AUDIT['total_rows'] == 70128
pdfmetrics.registerFont(TTFont('Malgun', 'C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold', 'C:/Windows/Fonts/malgunbd.ttf'))
pdfmetrics.registerFontFamily('Malgun', normal='Malgun', bold='MalgunBold', italic='Malgun', boldItalic='MalgunBold')
BLUE = colors.HexColor('#224C75')
TEAL = colors.HexColor('#167A80')
INK = colors.HexColor('#23313F')
LIGHT = colors.HexColor('#EEF4F8')
WIDTH = A4[0] - 100
styles = {
    'title': ParagraphStyle('title', fontName='MalgunBold', fontSize=22, leading=32, textColor=BLUE, spaceAfter=12, wordWrap='CJK'),
    'h1': ParagraphStyle('h1', fontName='MalgunBold', fontSize=15, leading=23, textColor=BLUE, spaceBefore=12, spaceAfter=9, wordWrap='CJK'),
    'h2': ParagraphStyle('h2', fontName='MalgunBold', fontSize=11, leading=17, textColor=BLUE, spaceBefore=9, spaceAfter=5, wordWrap='CJK'),
    'body': ParagraphStyle('body', fontName='Malgun', fontSize=10, leading=16.7, textColor=INK, spaceAfter=7, wordWrap='CJK'),
    'cell': ParagraphStyle('cell', fontName='Malgun', fontSize=8.6, leading=13.3, textColor=INK, wordWrap='CJK'),
    'small': ParagraphStyle('small', fontName='Malgun', fontSize=8.2, leading=13, textColor=colors.HexColor('#5A6875'), spaceAfter=6, wordWrap='CJK'),
}
story, plain = [], []


def p(text, style='body'):
    story.append(Paragraph(escape(text).replace('\n', '<br/>'), styles[style]))
    plain.append(text + '\n')


def table(rows, widths):
    plain.append('\n'.join(' | '.join(map(str, row)) for row in rows) + '\n')
    cells = [[Paragraph(escape(str(cell)).replace('\n', '<br/>'), styles['cell']) for cell in row] for row in rows]
    obj = Table(cells, colWidths=[WIDTH * w for w in widths], repeatRows=1, hAlign='LEFT')
    obj.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), .8, BLUE),
        ('LINEBELOW', (0, 1), (-1, -1), .35, colors.HexColor('#CDD8E0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.extend([obj, Spacer(1, 9)])


def page():
    story.append(PageBreak())
    plain.append('\n\f\n')


def coverage_figure():
    d = Drawing(WIDTH, 135)
    for i, f in enumerate(AUDIT['files']):
        y = 104 - i*26
        d.add(String(0, y+1, str(f['year']), fontName='MalgunBold', fontSize=10, fillColor=BLUE))
        d.add(Rect(54, y-3, 325, 17, fillColor=TEAL, strokeColor=None))
        d.add(String(62, y+1, f"01-01 ~ 12-31 / {f['unique_days']}일", fontName='Malgun', fontSize=8.5, fillColor=colors.white))
        d.add(String(390, y+1, f"{f['rows']:,}행", fontName='Malgun', fontSize=9, fillColor=INK))
    story.append(d)


def dst_figure():
    d = Drawing(WIDTH, 127)
    x0, y0 = 50, 24
    d.add(Line(x0, y0, WIDTH-20, y0, strokeColor=colors.HexColor('#9AAAB8')))
    for i, (label, n) in enumerate([('봄 전환일', 46), ('일반 날짜', 48), ('가을 전환일', 50)]):
        x = 104 + i*132
        height = n*1.4
        d.add(Rect(x, y0, 55, height, fillColor=TEAL if i != 1 else BLUE, strokeColor=None))
        d.add(String(x+27.5, y0+height+8, f'{n}구간', textAnchor='middle', fontName='MalgunBold', fontSize=10, fillColor=INK))
        d.add(String(x+27.5, 7, label, textAnchor='middle', fontName='Malgun', fontSize=9, fillColor=INK))
    d.add(String(0, 112, '단위: 30분 구간 수 / 세로축 기준 0', fontName='Malgun', fontSize=8, fillColor=INK))
    story.append(d)


# PAGE 1: template cover fields and overview
p('소형 LSTM을 활용한\n영국 전력수요 예측과 오차 원인 분석', 'title')
p('데이터 수집 단계 중간 보고서  |  작성 기준일: 2026-11-24', 'small')
table([
    ['항목', '내용', '항목', '내용'],
    ['프로젝트명', '영국 전력수요 예측', '팀명', '미기재'],
    ['학과(계열)', '미기재', '작성일', '2026-11-24'],
    ['이름 / 학번', '미기재 / 미기재', '진행 단계', '원본 수집·기본 검증 완료'],
], [.18, .36, .16, .30])
p('작성 범위', 'h2')
p('이 보고서는 원본 데이터 수집과 기본 품질 확인까지 실제 수행한 내용을 정리한다. 전처리 완료, 탐색적 분석 결과, 모델 학습 및 예측 성능은 아직 없으며 해당 항목은 계획 또는 미수행으로 표시하였다. 개인정보와 팀 정보는 확인되지 않아 임의로 작성하지 않았다.')
p('1. 프로그램 개요', 'h1')
p('1.1 프로젝트명', 'h2')
p('소형 LSTM을 활용한 영국 전력수요 예측과 오차 원인 분석')
p('1.2 프로젝트 개요', 'h2')
p('영국 NESO가 제공하는 2022~2025년 Great Britain 전력수요 자료를 이용하여 다음 30분의 National Demand를 예측하는 시계열 회귀 프로젝트이다. 간단한 기준모델과 소형 LSTM을 비교하고, 입력 기간과 시간 관련 변수의 영향을 검토할 예정이다. 평균적인 오차뿐 아니라 오차가 커지는 구간을 분석하여 모델의 한계와 개선 근거를 설명한다.')
p('1.3 주제 선정 배경 및 동기', 'h2')
p('수업에서 배운 순환신경망을 과거 관측이 다음 시점과 연결되는 문제에 적용하고자 하였다. 초미세먼지 실습과 겹치지 않고 최근 5년 이내의 해외 자료를 사용할 수 있어야 한다는 조건에 따라, 오래된 UCI 예제 대신 NESO의 2022~2025년 공개 자료를 선택하였다. 복잡한 모형보다 재현 가능한 실험과 이해 가능한 설명에 중점을 둔다.')
p('2. 문제정의 / 2.1 문제상황', 'h2')
p('다음 시간의 전력수요를 추정할 때 최근 값이나 전날 같은 시간의 값을 그대로 사용하는 방법이 간단한 출발점이 될 수 있다. 이 프로젝트는 LSTM이 이러한 기준보다 추가적인 예측 가치를 제공하는지 검증한다. 현재 자료에서 반복 패턴과 오차 원인은 아직 분석하지 않았으므로 확인할 가설로 둔다.')

# PAGE 2
page()
p('2. 문제정의: 분석 질문과 데이터 요구사항', 'h1')
p('2.2 주요 분석 질문', 'h2')
table([
    ['번호', '데이터로 확인할 질문', '판단 근거 / 현재 상태'],
    ['Q1', 'LSTM은 직전 값 및 전날 같은 시간 값보다 다음 30분의 수요를 더 정확히 예측하는가?', '동일 구간의 MAE·RMSE 비교\n현재: 미평가'],
    ['Q2', '과거 하루와 일주일 중 어느 입력 기간이 예측에 더 도움이 되는가?', '검증 연도에서 48·336구간 등 비교\n현재: 미실험'],
    ['Q3', '시간·요일 정보를 추가하면 성능이 개선되는가? 개선 후에도 오차가 큰 구간은 어디인가?', '변수 추가 전후 지표 및 시간대별 오차\n현재: 미분석'],
], [.08, .55, .37])
p('질문마다 동일한 검증 기준을 유지한다. 개별 실험에서 지표가 좋아졌더라도 다른 변수와 학습 조건을 함께 바꾸었다면 원인을 단정하지 않고 추가 비교가 필요한 결과로 기록한다.')
p('2.3 해결을 위한 데이터 요구사항 도출', 'h2')
table([
    ['필요 항목', '수집 목적', '출처 / 확보 상태'],
    ['정산 날짜·구간 번호', '시간순 정렬과 일정한 간격의 시계열 구성', 'NESO / 전 기간 확보'],
    ['National Demand(ND)', '다음 구간의 정답 및 과거 입력값', 'NESO / 전 기간 확보'],
    ['시간·요일·월', '일중·주중·계절 관련 정보의 효과 비교', '날짜·구간에서 생성 예정'],
    ['여러 해의 연속 자료', '학습·검증·평가를 시간순으로 분리', '2022~2025년 확보'],
    ['공휴일 정보', '필요 시 휴일 구간 오차 해석', '추가 후보 / 아직 수집하지 않음'],
], [.25, .40, .35])
p('요구 범위의 결정', 'h2')
p('초기 모델은 과거 ND와 시간 관련 변수 중심으로 제한한다. 날씨·공휴일 등 외부 자료를 확보하지 않은 상태에서 이미 사용한 것처럼 기술하지 않는다. 외부 자료를 추가한다면 예측 시점에 이용 가능한 정보인지, 날짜와 시간대가 일치하는지부터 확인한다.')
p('3. 데이터 수집 / 3.1 수집 대상 선정', 'h2')
p('NESO의 Historic Demand Data는 연도별 CSV와 공개 API 경로를 제공하며, 수집한 파일의 관측 연도가 모두 2022~2025년에 해당한다. 웹페이지 수정일과 실제 관측 기간을 구분하여 검사하였다. Great Britain은 잉글랜드·스코틀랜드·웨일스를 의미하며 북아일랜드를 포함한 영국 전체와는 구분한다. [1, 2]')

# PAGE 3
page()
p('3. 데이터 수집: 방법과 확보 결과', 'h1')
p('3.2 실제 수집 방법', 'h2')
p('공식 메타데이터 API에서 Historic Demand Data 2022~2025의 CSV 리소스를 확인한 뒤, 연도별 원본을 다운로드하였다. 임시 파일을 먼저 검증하고 통과한 파일을 원본 경로에 저장하였다. 해시, 바이트 수, 다운로드 시각, 공급자 수정 시각, 원본 URL과 리소스 ID를 함께 보관하였다. [2, 3]')
p('수집일은 2026-11-24(한국 시간)이다. 수집 코드는 Python 표준 라이브러리의 urllib.request, csv, datetime, hashlib 등을 사용하므로 별도 데이터 처리 패키지 설치 없이 재현할 수 있다.')
p('3.3 연도별 확보 현황', 'h2')
table([['파일명', '관측 기간', '행 수', '열 수', '크기(MB)']] + [
    [f"demanddata_{f['year']}.csv", f"{f['year']}-01-01 ~ 12-31", f"{f['rows']:,}", len(f['columns']), f"{f['bytes']/1_000_000:.3f}"] for f in AUDIT['files']
] + [['합계', '2022~2025년', '70,128', '연도별 상이', '7.095']], [.32, .27, .15, .10, .16])
p('그림 1. 연도별 원본 관측 기간 확보 현황', 'h2')
coverage_figure()
p('자료: collection_audit.json. 막대는 각 연도의 1월 1일~12월 31일 확보 여부를 표시하며 일별 날짜 누락은 없다. 2024년의 추가 48행은 윤년의 하루에 해당한다. 데이터 값의 예측 성능을 나타낸 그림은 아니다.', 'small')
p('3.4 이용 조건과 원본 보존', 'h2')
p('라이선스는 NESO Open Data Licence이며 보고서에 공급자와 출처를 명시한다. 이 파일의 주요 항목은 계통 수요·발전·연계선 관련 수치이며 학생·개인의 식별정보를 분석 대상으로 사용하지 않는다. 공급자는 과거 값을 사후 수정할 수 있으므로 현재 파일의 SHA256으로 수집 스냅샷을 식별한다. [1, 3]')
p('원본 4개 CSV는 data/raw/에 그대로 보관하였다. 저장소에는 수집 코드와 출처·검증 기록을 커밋하고 원본 CSV는 Git 제외 규칙을 적용하였다. 수집 단계 코드와 기록의 커밋은 b358a17(deeplearning)이다.')

# PAGE 4
page()
p('4. 데이터 확인 및 전처리', 'h1')
p('4.1 원본 데이터의 구성 및 변수 설명', 'h2')
table([
    ['변수', '자료 형태 / 단위', '의미와 향후 역할'],
    ['SETTLEMENT_DATE', '문자열 날짜', '현지 정산일. 연도별 표기 형식을 해석해야 한다.'],
    ['SETTLEMENT_PERIOD', '정수 / 구간 번호', '현지 정산일 내 30분 구간. 날짜와 함께 유일키로 확인하였다.'],
    ['ND', '수치 / MW', 'National Demand. 다음 구간의 예측 대상이며 과거 값은 입력 후보이다.'],
    ['TSD', '수치 / MW', 'Transmission System Demand. ND와 정의가 달라 동일한 목표로 혼용하지 않는다.'],
    ['EMBEDDED_WIND_GENERATION', '수치 / MW', '추정 분산형 풍력 발전량. 이번 단계에서는 모델 입력으로 사용하지 않았다.'],
    ['EMBEDDED_SOLAR_GENERATION', '수치 / MW', '추정 분산형 태양광 발전량. 이번 단계에서는 모델 입력으로 사용하지 않았다.'],
], [.34, .20, .46])
p('ND는 계량된 발전량의 합에서 발전소 자체 소비, 양수 펌핑, 연계선 수출에 필요한 발전량 등을 제외한 NESO의 수요 지표이다. 가정 소비만을 뜻하거나 모든 최종소비를 직접 측정한 값이라고 해석하지 않는다. MW는 전력 단위로, 에너지량인 MWh와 구분한다. [1]')
p('4.2 결측치·중복값·이상치 확인', 'h2')
table([
    ['검사 항목', '실제 확인 결과', '현재 처리'],
    ['빈 값·NA 계열 표시', '모든 연도의 모든 컬럼에서 0건', '삭제·대체 없음'],
    ['날짜·구간 중복', '연도별 유일키 중복 0건', '중복 제거 없음'],
    ['날짜 범위·일별 누락', '전 기간 확보, 범위 밖 날짜 0건', '추가 수집 없음'],
    ['ND의 자료형·유효 범위', '수치 변환 가능, 비유한 값·0 이하 0건', '값 변경 없음'],
    ['도메인상 이상치', '정밀 분석 미수행', '이상치 제거 없음'],
], [.31, .42, .27])
p('빈 값이 없다는 결과는 모든 값이 정확하다는 의미가 아니다. 다른 컬럼의 0이 실제 관측인지 미제공 표시인지, ND 급등락이 오류인지 실제 현상인지는 별도의 의미 검토가 필요하다. 자료를 삭제하기 전에 그 근거를 확보할 예정이다.')

# PAGE 5
page()
p('4.3 자료형과 시간축에서 발견한 문제 및 대응', 'h1')
p('이슈 1. 같은 날짜 변수가 서로 다른 문자열로 저장됨', 'h2')
p('문제: 2022·2024년은 01-JAN-2022 같은 형태, 2023년은 01-Jan-23, 2025년은 2025-01-01 형태였다. 최초 검증 코드가 이 표기를 모두 지원하지 않아 날짜 파싱이 실패하였다. 이는 관측값 결측이 아니라 읽기 규칙과 원본 표현이 맞지 않은 문제였다.')
p('대응·확인 결과: 날짜 형식을 명시적으로 추가하고 재검증하였다. 네 연도 모두 실제 연도의 시작일부터 마지막 날까지 해석되었다. 검증 중 메모리에서만 날짜형으로 변환했으며 원본 CSV 문자열은 변경하지 않았다.')
p('이슈 2. 연도별 컬럼 수가 다름', 'h2')
p('문제: 2022년은 21열이고 2023~2025년은 22열이다. SCOTTISH_TRANSFER의 유무가 차이를 만든다. 전체 스키마가 같다고 가정하면 병합 시 불필요한 결측 컬럼이 생기거나 입력 배열의 위치가 달라질 수 있다.')
p('대응·확인 결과: 날짜·정산 구간·ND가 모든 해에 있는지 필수 컬럼 기준으로 검증하고 전체 스키마의 차이는 별도로 기록하였다. 행 결합이나 누락 컬럼 채우기는 아직 하지 않았다. 이후 모델에 쓸 공통 컬럼을 이름으로 선택할 예정이다.')
p('이슈 3. 하루의 30분 구간 수가 항상 48개는 아님', 'h2')
p('문제: 각 연도에서 46구간인 날과 50구간인 날이 하나씩 확인되었다. 무조건 48행을 기대하면 정상적인 서머타임 전환일을 누락 또는 중복으로 오인할 수 있다.')
dst_figure()
p('그림 2. 일반 날짜와 서머타임 전환일의 구간 수. 단위: 30분 구간. 각 연도에 봄 46구간·가을 50구간인 날이 하나씩 관측됐다. 자료: collection_audit.json.', 'small')
p('대응·확인 결과: 봄·가을 전환일의 기대 구간 수를 달리 검사하였다. 실제 46·50구간 날짜는 전환일과 일치하며 구간 번호의 누락·중복은 없었다. 단, 실제 UTC 시간축 변환과 연속 30분 간격 검사는 다음 전처리 단계에 남아 있다.')

# PAGE 6
page()
p('4.4 현재 처리 결과 요약', 'h1')
table([
    ['구분', '현재 상태'],
    ['수집 전 → 수집 후', '대상 원본 미확보 → CSV 4개, 총 70,128행 확보'],
    ['수집된 원본 → 현재 보관본', '행·열·값 변경 없음. 원본 4개를 그대로 보존'],
    ['제외된 관측 / 대체한 값', '0행 / 0건'],
    ['검증용 자료형 해석', '날짜·정산 구간·ND를 메모리에서 해석하여 검사'],
    ['아직 생성하지 않은 산출물', '통합·정제 파일, UTC 시간축, 파생변수, 학습 시퀀스'],
    ['모델에 쓸 최종 입력변수', '미확정. 과거 ND 및 시간·요일 변수 중심으로 검토 예정'],
], [.36, .64])
p('검증을 위한 자료형 변환과 학습용 데이터 전처리 완료는 구분해야 한다. 이번 단계는 읽기와 기본 구조 확인까지이며, 원본을 변형한 processed 파일은 아직 없다.')
p('5. 탐색적 데이터 분석(EDA) - 미수행 / 계획', 'h1')
p('5.1 기초 통계 및 데이터 분포', 'h2')
p('수집 행 수와 결측·중복 수는 확보하였다. 예측 문제를 설명하기 위한 ND 분포, 평균·중앙값·분산 및 히스토그램은 아직 작성하지 않았다. 우선 학습 기간의 분포와 단위를 확인하고 급격한 변화 구간의 의미를 살펴볼 예정이다.')
p('5.2 집단별 비교 및 시간에 따른 변화', 'h2')
p('시간대·요일·월별 평균과 표본 수, 평일·주말 차이 및 시간 흐름을 그래프로 확인할 계획이다. 현재 일중·계절 패턴이 실제로 얼마나 강한지는 결론을 내리지 않았다.')
p('5.3 변수 간 관계 탐색', 'h2')
p('현재 ND와 과거 ND의 관계를 시차별 산점도나 상관분석으로 살펴볼 예정이다. 관계가 보이더라도 인과관계나 예측 성능 개선으로 곧바로 해석하지 않고 검증 실험으로 확인한다.')
p('5.4 주요 분석 질문에 대한 중간 결과', 'h2')
p('Q1~Q3의 답은 아직 유보한다. 이번 수집에서는 질문을 검증할 기간과 필수 변수를 확보했다는 점만 확인하였다. 본문 그림 1·2는 수집 품질을 설명하는 도표이며 수요 패턴이나 모델 성능을 분석한 결과는 아니다.')

# PAGE 7
page()
p('6. 예측모델 설계 및 구축 - 미수행 / 계획', 'h1')
p('6.1 예측 목표 및 변수 선정', 'h2')
p('현재 구간까지 관측된 ND로 다음 30분 구간의 ND(MW)를 예측하는 회귀 문제로 설정한다. 입력 후보는 과거 ND와 예측 시점에 알 수 있는 시간·요일 정보이다. 미래 시점의 실제 발전량 등 사후에만 아는 값이 입력에 들어가지 않도록 점검한다.')
p('6.2 학습·평가 데이터 분리', 'h2')
table([
    ['구분', '기간', '원본 행 수', '사용 목적'],
    ['학습 예정', '2022~2023년', '35,040', '모델 가중치·전처리 기준 학습'],
    ['검증 예정', '2024년', '17,568', '변수·입력 길이·구조 선택'],
    ['최종 평가 예정', '2025년', '17,520', '선택 완료 후 최종 성능 확인'],
], [.20, .21, .17, .42])
p('표는 원본 기준 건수이며 시퀀스 생성 뒤의 학습 표본 수는 아직 확정되지 않았다. 데이터를 무작위로 섞어 연도 구분을 무너뜨리지 않는다. 표준화 기준은 학습 자료에서만 구하고 검증·평가 자료에 적용할 예정이다.', 'small')
p('6.3 기준모델 및 예측모델 선정', 'h2')
p('학습 기간 평균, 직전 값, 전날 같은 시간 값을 기준모델로 두고 선형회귀와 소형 LSTM을 비교할 계획이다. LSTM은 1개 층·은닉 유닛 16~32개에서 시작한다. 복잡도를 높이기 전에 단순 기준보다 예측 가치가 있는지 확인한다. 전날 같은 시간 기준은 서머타임을 반영한 대응 시점을 정의해야 한다.')
p('6.4 모델 학습 과정 및 설정', 'h2')
p('학습은 아직 실행하지 않았다. 향후 PyTorch 기반의 설명 가능한 학습 루프를 구성하고, 입력 길이·학습률·배치 크기·seed·조기 종료 기준과 라이브러리 버전을 기록한다. 입력 기간은 48구간(하루)과 336구간(일주일) 등을 검증 자료에서 비교할 예정이다.')
p('7. 예측모델 평가 및 결과 분석 - 미수행 / 계획', 'h1')
p('7.1~7.2 평가 지표와 성능 비교', 'h2')
p('MAE는 평균적으로 얼마나 틀렸는지, RMSE는 큰 오차가 얼마나 있는지를 MW 단위로 평가하며 모두 작을수록 좋다. 동일한 평가 구간과 정답에 대해 비교한다. 현재 계산한 예측값·성능값이 없어 모델별 수치는 기재하지 않는다.')
p('7.3~7.4 시각화·오류 분석·개선 방향', 'h2')
p('실제값과 예측값, 시간대별 오차, 큰 오차 사례 및 학습·검증 곡선을 제시할 예정이다. 실제 관측한 문제를 근거로 입력 길이·변수·모델 크기를 한 번에 하나씩 바꾸고 개선되지 않은 시도도 기록한다. 2025년 최종 평가값을 보며 반복 조정하지 않는다.')

# PAGE 8
page()
p('8. 결론 - 데이터 수집 단계', 'h1')
p('최근 해외 자료를 사용한다는 조건에 맞춰 NESO의 2022~2025년 원본 4개, 총 70,128행을 확보하였다. 빈 값·NA 계열 표시와 날짜·구간 중복은 없었으며 날짜 범위와 서머타임 구간 수 검사를 통과하였다. 다만 연도별 날짜 표기와 컬럼 차이를 확인하여 읽기 규칙을 수정하고 후속 전처리 과제로 기록하였다.')
p('이 단계에서 Q1(LSTM의 비교 우위), Q2(적절한 입력 기간), Q3(시간 변수의 효과와 오류 구간)에는 아직 답할 수 없다. 데이터 확보가 완료되었다는 사실과 예측 가능성 또는 성능 개선이 입증되었다는 주장을 구분한다. 다음 단계는 시간축 구성과 학습용 자료 준비이다.')
p('9. 팀원 역할 및 학습 소감', 'h1')
p('팀 구성과 실제 역할 분담, 개인 학습 소감은 제공되지 않아 미기재로 둔다. 현재 작업의 기술적 고찰로는 ① 같은 공급자의 자료도 연도별 표현과 컬럼이 달라질 수 있음 ② 서머타임으로 정상적인 하루 구간 수가 달라짐 ③ 원본 보존과 검증 기록이 재현에 필요함을 정리할 수 있다. 개인 소감은 작성자가 확인 후 추가한다.')
p('10. 참고자료 및 부록', 'h1')
p('원본 양식은 “9. 팀원 역할 및 학습 소감” 다음에 “9. 참고자료 및 부록”으로 번호가 중복되어 있어, 이 보고서에서는 참고자료를 10번으로 정리하였다.', 'small')
p('[1] NESO, Historic Demand Data 및 연도별 변수 설명.\nhttps://www.neso.energy/data-portal/historic-demand-data\n[2] NESO 공식 메타데이터 응답(수집일: 2026-11-24).\nhttps://api.neso.energy/api/3/action/package_show?id=historic-demand-data\n[3] 수집 스냅샷: data/metadata/download_manifest.json, source_package.json, collection_audit.json.\n[4] 사용자 제공 보고서 양식: 딥러닝_프로젝트최종보고서.pdf.\n[5] 수업 자료: RNN.pdf, 딥러닝1_다층신경망.pdf, 3_선형회귀.pdf. 계획의 학습 범위 참고 자료이며 실험 결과의 근거로 사용하지 않았다.', 'small')
p('10.1 코드와 실행 방법', 'h2')
p(f'수집: scripts/collect_data.py / 원본: data/raw/demanddata_2022.csv ~ demanddata_2025.csv\n재검증: 프로젝트 폴더에서 python scripts/collect_data.py --offline\n보고서 생성: python scripts/make_collection_report.py\n작성 환경: Python {platform.python_version()}, ReportLab {Version}. 수집 검증은 표준 라이브러리만 사용.', 'small')
p('10.2 현재 산출물과 다음 작업', 'h2')
p('현재: 원본 CSV 4개, 수집·검증 코드, 메타데이터·해시 기록, 데이터 수집 문서, 본 중간 보고서.\n다음: UTC 시간축 및 간격 검사 → 학습 자료 EDA → 기준모델·LSTM 학습 → 검증 기반 개선 → 최종 평가와 보고서 확장. 최종 보고서는 실험 근거와 시각화를 추가하여 약 15쪽으로 구성할 예정이다.', 'small')


def footer(canvas, doc):
    canvas.setTitle('영국 전력수요 예측 - 데이터 수집 단계 중간 보고서')
    canvas.setAuthor('GB Electricity LSTM Project')
    canvas.setStrokeColor(colors.HexColor('#C4D1DD'))
    canvas.line(50, 42, A4[0]-50, 42)
    canvas.setFont('Malgun', 8)
    canvas.setFillColor(colors.HexColor('#5A6875'))
    canvas.drawString(50, 28, '데이터 수집 단계 | 2026-11-24 | 미수행 결과는 계획으로 구분')
    canvas.drawRightString(A4[0]-50, 28, f'{doc.page}')


pdf_path = OUT / 'gb_electricity_collection_report.pdf'
doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=50, rightMargin=50,
                        topMargin=42, bottomMargin=57, title='영국 전력수요 예측 중간 보고서')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
(OUT / 'gb_electricity_collection_report.txt').write_text('\n'.join(plain), encoding='utf-8')
print(pdf_path)
