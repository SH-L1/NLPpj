const path = require("path");
const fs = require("fs");
const PptxGenJS = require("C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/pptxgenjs@4.0.1/node_modules/pptxgenjs");

const ROOT = "C:/Users/user/Documents/GitHub/NLPpj";
const OUT = path.join(ROOT, "submissions", "국민청원_장문텍스트_분류_최종발표.pptx");

const pptx = new PptxGenJS();
pptx.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
pptx.layout = "WIDE";
pptx.author = "NLPpj";
pptx.subject = "국민청원 장문 텍스트 분류 최종 발표";
pptx.title = "국민청원 장문 텍스트 분류 NLP 프로젝트";
pptx.lang = "ko-KR";

const F = {
  display: "Noto Serif KR",
  sans: "Noto Sans KR",
  mono: "Cascadia Code",
};

pptx.theme = {
  headFontFace: F.display,
  bodyFontFace: F.sans,
  lang: "ko-KR",
};

const C = {
  bg: "F7F3EA",
  panel: "FFFDF8",
  ink: "151B20",
  muted: "69737C",
  line: "D7CBBE",
  dark: "10262D",
  accent: "0D6B66",
  accentSoft: "DCECE7",
  rust: "B65A35",
  rustSoft: "F0DED3",
  violet: "6958A8",
  violetSoft: "E5DFF2",
  gold: "E5A84C",
  code: "0E1D22",
  white: "FFFFFF",
};

const W = 13.333;
const H = 7.5;
const M = 0.68;

function rect(slide, x, y, w, h, fill, line = fill, width = 0) {
  slide.addShape(pptx.ShapeType.rect, { x, y, w, h, fill: { color: fill }, line: { color: line, width } });
}

function line(slide, x, y, w, color = C.line, width = 1) {
  slide.addShape(pptx.ShapeType.line, { x, y, w, h: 0, line: { color, width } });
}

function deckBg(slide, n, dark = false) {
  rect(slide, 0, 0, W, H, dark ? C.dark : C.bg);
  slide.addText(String(n).padStart(2, "0"), {
    x: 12.25, y: 0.47, w: 0.42, h: 0.16,
    fontFace: F.sans, fontSize: 7.5, bold: true,
    color: dark ? "B7CCC8" : C.muted, align: "right", margin: 0,
  });
}

function label(slide, text, x = M, y = 0.45, dark = false) {
  slide.addText(text, {
    x, y, w: 2.4, h: 0.17,
    fontFace: F.sans, fontSize: 7.5, bold: true, charSpace: 1.35,
    color: dark ? C.gold : C.accent, margin: 0,
  });
}

function title(slide, text, x = M, y = 0.8, w = 11.0, dark = false, size = 24) {
  slide.addText(text, {
    x, y, w, h: 0.78,
    fontFace: F.display, fontSize: size, bold: true,
    color: dark ? C.white : C.ink, margin: 0, fit: "shrink",
  });
}

function footer(slide, text, dark = false) {
  line(slide, M, 6.86, 11.95, dark ? "315157" : C.line, 0.65);
  slide.addText(text, {
    x: M, y: 7.03, w: 8.5, h: 0.17,
    fontFace: F.sans, fontSize: 7.3,
    color: dark ? "B7CCC8" : C.muted, margin: 0,
  });
}

function highlightText(slide, parts, x, y, w, h, size = 12, dark = false) {
  slide.addText(parts, {
    x, y, w, h,
    fontFace: F.sans, fontSize: size,
    color: dark ? "D9E4E2" : C.ink,
    margin: 0, fit: "shrink", breakLine: false,
    paraSpaceAfterPt: 7,
  });
}

function metricCard(slide, x, y, w, h, name, value, trend, color = C.accent) {
  rect(slide, x, y, w, h, C.panel, C.line, 0.65);
  slide.addText(name, { x: x + 0.18, y: y + 0.18, w: w - 0.36, h: 0.18, fontFace: F.sans, fontSize: 8.2, color: C.muted, margin: 0, fit: "shrink" });
  slide.addText(value, { x: x + 0.18, y: y + 0.48, w: w - 0.36, h: 0.42, fontFace: F.sans, fontSize: 22, bold: true, color, margin: 0, fit: "shrink" });
  slide.addText(trend, { x: x + 0.18, y: y + 1.03, w: w - 0.36, h: 0.18, fontFace: F.sans, fontSize: 7.7, bold: true, color, margin: 0, fit: "shrink" });
}

function tocItem(slide, num, head, desc, x, y) {
  slide.addText(num, { x, y, w: 0.52, h: 0.26, fontFace: F.sans, fontSize: 14, bold: true, color: C.accent, margin: 0 });
  slide.addText(head, { x: x + 0.75, y: y - 0.01, w: 3.6, h: 0.23, fontFace: F.display, fontSize: 12.2, bold: true, color: C.ink, margin: 0, fit: "shrink" });
  slide.addText(desc, { x: x + 0.75, y: y + 0.33, w: 4.3, h: 0.18, fontFace: F.sans, fontSize: 7.8, color: C.muted, margin: 0, fit: "shrink" });
  line(slide, x + 0.75, y + 0.68, 4.55, C.line, 0.55);
}

function comparisonColumn(slide, x, y, w, h, head, items, tone) {
  rect(slide, x, y, w, h, tone === "after" ? C.accentSoft : C.panel, tone === "after" ? C.accent : C.line, tone === "after" ? 1.1 : 0.7);
  slide.addText(head, { x: x + 0.28, y: y + 0.28, w: w - 0.56, h: 0.25, fontFace: F.display, fontSize: 15, bold: true, color: tone === "after" ? C.accent : C.rust, margin: 0 });
  items.forEach((it, i) => {
    slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.33, y: y + 0.88 + i * 0.45, w: 0.08, h: 0.08, fill: { color: tone === "after" ? C.accent : C.rust }, line: { color: tone === "after" ? C.accent : C.rust } });
    slide.addText(it, { x: x + 0.55, y: y + 0.78 + i * 0.45, w: w - 0.85, h: 0.25, fontFace: F.sans, fontSize: 8.8, color: C.ink, margin: 0, fit: "shrink" });
  });
}

function step(slide, x, y, num, head, desc) {
  rect(slide, x, y, 1.9, 1.28, C.panel, C.line, 0.65);
  slide.addText(num, { x: x + 0.15, y: y + 0.14, w: 0.35, h: 0.17, fontFace: F.sans, fontSize: 8.0, bold: true, color: C.accent, margin: 0 });
  slide.addText(head, { x: x + 0.15, y: y + 0.46, w: 1.55, h: 0.24, fontFace: F.display, fontSize: 12.5, bold: true, color: C.ink, margin: 0, fit: "shrink" });
  slide.addText(desc, { x: x + 0.15, y: y + 0.86, w: 1.55, h: 0.22, fontFace: F.sans, fontSize: 7.8, color: C.muted, margin: 0, fit: "shrink" });
}

function arrow(slide, x, y) {
  slide.addShape(pptx.ShapeType.line, { x, y, w: 0.55, h: 0, line: { color: C.rust, width: 1.1, endArrowType: "triangle" } });
}

function barChart(slide, x, y, w, h, data) {
  const max = Math.max(...data.map((d) => d.value));
  line(slide, x, y + h, w, C.line, 0.65);
  data.forEach((d, i) => {
    const bw = 0.52;
    const gap = (w - data.length * bw) / (data.length - 1);
    const bx = x + i * (bw + gap);
    const bh = (h - 0.55) * d.value / max;
    slide.addText(d.label, { x: bx - 0.07, y: y + h + 0.16, w: 0.66, h: 0.18, fontFace: F.sans, fontSize: 7.5, color: C.muted, align: "center", margin: 0 });
    slide.addText(d.text, { x: bx - 0.12, y: y + h - bh - 0.32, w: 0.76, h: 0.16, fontFace: F.sans, fontSize: 7.3, bold: true, color: d.color, align: "center", margin: 0 });
    rect(slide, bx, y + h - bh, bw, bh, d.color);
  });
}

function table(slide, x, y, colW, rows, opts = {}) {
  const rowH = opts.rowH || 0.38;
  const total = colW.reduce((a, b) => a + b, 0);
  rows.forEach((row, r) => {
    const yy = y + r * rowH;
    const header = r === 0;
    const emph = opts.emph?.includes(r);
    rect(slide, x, yy, total, rowH, header ? C.dark : emph ? C.accentSoft : C.panel, header ? C.dark : C.panel);
    let xx = x;
    row.forEach((cell, c) => {
      const accent = opts.accent?.some(([rr, cc]) => rr === r && cc === c);
      slide.addText(cell, {
        x: xx + 0.08, y: yy + 0.1, w: colW[c] - 0.16, h: 0.15,
        fontFace: F.sans, fontSize: opts.size || 7.8,
        bold: header || emph || accent,
        color: header ? C.white : accent ? C.accent : C.ink,
        align: c > 0 ? "right" : "left",
        margin: 0, fit: "shrink",
      });
      xx += colW[c];
    });
    if (!header) line(slide, x, yy + rowH, total, C.line, 0.5);
  });
}

function donut(slide, x, y, values, centerText, centerLabel) {
  // Simplified template-like donut: layered arcs are approximated with colored rings.
  const colors = [C.accent, C.rust, C.violet, C.gold];
  values.forEach((v, i) => {
    slide.addShape(pptx.ShapeType.arc, {
      x: x + i * 0.02, y: y + i * 0.02, w: 2.15 - i * 0.04, h: 2.15 - i * 0.04,
      adjustPoint: 0.15 + i * 0.12,
      line: { color: colors[i], width: 12 },
    });
  });
  slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.54, y: y + 0.54, w: 1.07, h: 1.07, fill: { color: C.bg }, line: { color: C.bg } });
  slide.addText(centerText, { x: x + 0.52, y: y + 0.82, w: 1.1, h: 0.23, fontFace: F.sans, fontSize: 14, bold: true, color: C.ink, align: "center", margin: 0 });
  slide.addText(centerLabel, { x: x + 0.55, y: y + 1.08, w: 1.05, h: 0.16, fontFace: F.sans, fontSize: 7.2, color: C.muted, align: "center", margin: 0 });
}

function codeBlock(slide, x, y, w, h, filename, code) {
  rect(slide, x, y, w, h, C.code, "284149", 0.85);
  rect(slide, x, y, w, 0.42, "17313A", "17313A");
  [0, 1, 2].forEach((i) => slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.18 + i * 0.18, y: y + 0.16, w: 0.07, h: 0.07, fill: { color: i === 0 ? C.rust : i === 1 ? C.gold : C.accent }, line: { color: i === 0 ? C.rust : i === 1 ? C.gold : C.accent } }));
  slide.addText(filename, { x: x + 0.75, y: y + 0.13, w: 1.8, h: 0.15, fontFace: F.sans, fontSize: 7.3, color: "BFD5D2", margin: 0 });
  slide.addText(code, { x: x + 0.22, y: y + 0.58, w: w - 0.44, h: h - 0.74, fontFace: F.mono, fontSize: 6.8, color: "EAF3F1", margin: 0, fit: "shrink" });
}

function mediaBox(slide, x, y, w, h, title, file) {
  rect(slide, x, y, w, h, C.panel, C.line, 0.9);
  slide.addText("IMAGE PLACEHOLDER · 16:9", { x, y: y + h / 2 - 0.08, w, h: 0.16, fontFace: F.sans, fontSize: 8.5, bold: true, color: C.muted, align: "center", margin: 0 });
  slide.addText(title, { x: x + 0.22, y: y + 0.23, w: w - 0.44, h: 0.2, fontFace: F.display, fontSize: 11.5, bold: true, color: C.ink, margin: 0, fit: "shrink" });
  slide.addText(file, { x: x + 0.22, y: y + h - 0.42, w: w - 0.44, h: 0.16, fontFace: F.sans, fontSize: 7.2, color: C.muted, margin: 0, fit: "shrink" });
}

function slide1() {
  const s = pptx.addSlide(); deckBg(s, 1, true);
  s.addText("NLP REPORT · 2026", { x: M, y: 0.82, w: 3.0, h: 0.18, fontFace: F.sans, fontSize: 8, bold: true, charSpace: 1.2, color: C.gold, margin: 0 });
  s.addText("국민청원 장문 텍스트\n분류 프로젝트", { x: M, y: 1.45, w: 7.2, h: 1.15, fontFace: F.display, fontSize: 33, bold: true, color: C.white, margin: 0, fit: "shrink" });
  s.addText("전처리 · 모델링 · Transformer fine-tuning · 오분류 분석", { x: M, y: 3.0, w: 5.4, h: 0.22, fontFace: F.sans, fontSize: 10.5, color: "C9DAD7", margin: 0 });
  metricCard(s, 0.75, 4.25, 1.85, 1.28, "Final F1", "0.8847", "target 0.88 achieved", C.gold);
  metricCard(s, 2.9, 4.25, 1.85, 1.28, "Improvement", "+0.0912", "vs best baseline", C.gold);
  metricCard(s, 5.05, 4.25, 1.85, 1.28, "Scope", "11", "slides / 5 min", C.gold);
  mediaBox(s, 7.55, 0.95, 4.65, 4.9, "프로젝트 구조 또는 데이터 예시", "README.md 또는 data/raw/train.csv 캡처");
  footer(s, "Metrics · Visualization · Insights · Analysis", true);
}

function slide2() {
  const s = pptx.addSlide(); deckBg(s, 2); label(s, "AGENDA"); title(s, "Table of Contents");
  tocItem(s, "01", "Problem & Data", "장문 국민청원 데이터와 품질 리스크", 1.2, 1.9);
  tocItem(s, "02", "Preprocessing & Control", "전처리 근거와 동일 split 실험 통제", 1.2, 3.0);
  tocItem(s, "03", "Model Comparison", "TF-IDF, LSTM, Transformer 비교", 1.2, 4.1);
  tocItem(s, "04", "Results & Errors", "macro F1, Confusion Matrix, 오분류 해석", 7.05, 1.9);
  tocItem(s, "05", "Conclusion", "성과와 후속 개선 로드맵", 7.05, 3.0);
  footer(s, "발표 흐름은 교수님 요구사항인 코드 흐름, 파라미터 근거, 결과 해석을 직접 설명하는 구조로 구성");
}

function slide3() {
  const s = pptx.addSlide(); deckBg(s, 3); label(s, "ANALYSIS"); title(s, "국민청원 본문은 짧은 문장이 아니라 사회 이슈가 섞인 장문 분류 문제다.");
  highlightText(s, [
    { text: "데이터는 train ", options: {} },
    { text: "40,000건", options: { bold: true, color: C.accent } },
    { text: ", test ", options: {} },
    { text: "5,000건", options: { bold: true, color: C.rust } },
    { text: "으로 구성된다. 청원 본문은 평균 ", options: {} },
    { text: "546.05자", options: { bold: true, color: C.violet } },
    { text: "이며 최대 32,767자까지 길어져 RNN/LSTM의 입력 길이 제한과 Transformer truncation이 모두 중요한 설계 이슈가 된다.", options: {} },
  ], 0.95, 2.0, 5.4, 2.2, 14);
  metricCard(s, 7.1, 1.75, 1.6, 1.2, "Train", "40K", "labeled rows", C.accent);
  metricCard(s, 8.95, 1.75, 1.6, 1.2, "Test", "5K", "submission rows", C.rust);
  metricCard(s, 10.8, 1.75, 1.6, 1.2, "Classes", "3", "target labels", C.violet);
  comparisonColumn(s, 7.1, 3.55, 2.45, 1.65, "Risk", ["장문 본문", "사회 이슈 중첩", "라벨 경계 혼동"], "before");
  comparisonColumn(s, 9.9, 3.55, 2.45, 1.65, "Response", ["정제 규칙", "동일 split", "Transformer 비교"], "after");
  footer(s, "핵심은 단순 정확도보다 장문 문맥과 라벨 경계에 대한 설명 가능성");
}

function slide4() {
  const s = pptx.addSlide(); deckBg(s, 4); label(s, "COMPARISON"); title(s, "라벨은 균형적이지만 결측·중복·긴 본문이 모델링 리스크다.");
  comparisonColumn(s, 0.95, 1.85, 4.25, 3.35, "Before preprocessing", ["결측 본문 8건", "중복 본문 637건", "최대 길이 32,767자", "상위 토큰에 청원 관용 표현 포함"], "before");
  comparisonColumn(s, 5.65, 1.85, 4.25, 3.35, "After preprocessing", ["정제 후 train 39,272건", "HTML/URL/email 제거", "도메인 불용어 관리", "동일 조건의 모델 비교 가능"], "after");
  mediaBox(s, 10.45, 1.85, 2.05, 3.35, "EDA chart", "category_distribution.png 또는 text_length_distribution.png");
  footer(s, "기본 표 대신 before/after 비교 구조로 데이터 품질 개선 논리를 명확히 표현");
}

function slide5() {
  const s = pptx.addSlide(); deckBg(s, 5); label(s, "PROCESS"); title(s, "전처리부터 평가까지 하나의 재현 가능한 파이프라인으로 구성했다.");
  const y = 2.25;
  step(s, 0.85, y, "01", "EDA", "분포·결측·길이 확인");
  arrow(s, 2.95, y + 0.64);
  step(s, 3.65, y, "02", "Clean", "본문 정규화와 중복 제거");
  arrow(s, 5.75, y + 0.64);
  step(s, 6.45, y, "03", "Model", "baseline과 Transformer 학습");
  arrow(s, 8.55, y + 0.64);
  step(s, 9.25, y, "04", "Analyze", "F1과 오분류 해석");
  highlightText(s, [
    { text: "전처리는 ", options: {} },
    { text: "HTML, URL, email, 특수문자", options: { bold: true, color: C.rust } },
    { text: "를 제거하고, 청원 도메인 불용어를 줄여 모델이 실제 분류 신호에 집중하도록 설계했다.", options: {} },
  ], 1.25, 4.85, 9.7, 0.6, 10);
  footer(s, "Each stage feeds into the next · preprocessing choices are recorded in code and report");
}

function slide6() {
  const s = pptx.addSlide(); deckBg(s, 6); label(s, "KEY METRICS"); title(s, "전처리와 실험 통제는 수치로 검증 가능한 상태로 기록했다.");
  metricCard(s, 1.0, 2.0, 2.25, 1.45, "Clean train", "39,272", "40,000 raw rows", C.accent);
  metricCard(s, 3.65, 2.0, 2.25, 1.45, "Mean length", "524.48", "after cleaning", C.rust);
  metricCard(s, 6.3, 2.0, 2.25, 1.45, "Vocabulary", "140,755", "min_df/max_df selected", C.violet);
  metricCard(s, 8.95, 2.0, 2.25, 1.45, "Seed", "42", "same split control", C.gold);
  const rows = [["parameter", "value", "reason"], ["min_df", "3", "희소 잡음 제거"], ["max_df", "0.85", "범용 표현 제거"], ["split", "70/15/15", "공정 비교"], ["metric", "macro F1", "클래스 균형 평가"]];
  table(s, 1.35, 4.25, [1.55, 1.2, 4.8], rows, { emph: [1, 2], accent: [[1, 1], [2, 1]], rowH: 0.38 });
  footer(s, "교수님 질문 대비: 파라미터 선택 이유를 코드와 보고서의 같은 수치로 설명");
}

function slide7() {
  const s = pptx.addSlide(); deckBg(s, 7); label(s, "DATA VISUALIZATION"); title(s, "모델 비교는 baseline에서 Transformer로 이어지는 성능 개선을 보여준다.");
  barChart(s, 1.05, 2.05, 5.0, 3.0, [
    { label: "TF-IDF", value: 0.7934, text: "0.7934", color: C.accent },
    { label: "LSTM", value: 0.7201, text: "0.7201", color: C.rust },
    { label: "Transformer", value: 0.8847, text: "0.8847", color: C.violet },
  ]);
  metricCard(s, 7.1, 1.8, 1.9, 1.28, "Final F1", "0.8847", "target achieved", C.violet);
  metricCard(s, 9.35, 1.8, 1.9, 1.28, "vs baseline", "+0.0912", "best baseline", C.rust);
  metricCard(s, 7.1, 3.45, 1.9, 1.28, "vs LSTM", "+0.1646", "sequence model", C.accent);
  metricCard(s, 9.35, 3.45, 1.9, 1.28, "Runtime", "427s", "CUDA run", C.gold);
  footer(s, "Green/Rust/Violet 색상 체계를 모델 비교 전반에 일관되게 적용");
}

function slide8() {
  const s = pptx.addSlide(); deckBg(s, 8); label(s, "DISTRIBUTION"); title(s, "오분류는 특정 모델 오류보다 사회정책 의미가 겹치는 라벨 경계에서 발생했다.");
  donut(s, 1.25, 2.05, [40, 25, 20], "679", "major errors");
  const items = [["육아/교육 → 건강/복지", "230", "11.69%", C.accent], ["건강/복지 → 문화/언론", "141", "7.25%", C.rust], ["건강/복지 → 육아/교육", "106", "5.45%", C.violet]];
  items.forEach(([a, b, c, col], i) => {
    const y = 2.0 + i * 0.78;
    s.addShape(pptx.ShapeType.rect, { x: 4.5, y: y + 0.06, w: 0.14, h: 0.14, fill: { color: col }, line: { color: col } });
    s.addText(a, { x: 4.78, y, w: 3.5, h: 0.2, fontFace: F.sans, fontSize: 8.5, color: C.ink, margin: 0, fit: "shrink" });
    s.addText(b, { x: 8.6, y, w: 0.6, h: 0.2, fontFace: F.sans, fontSize: 8.7, bold: true, color: col, align: "right", margin: 0 });
    s.addText(c, { x: 9.45, y, w: 0.75, h: 0.2, fontFace: F.sans, fontSize: 8.7, bold: true, color: col, align: "right", margin: 0 });
  });
  mediaBox(s, 4.5, 4.75, 5.95, 1.15, "Confusion Matrix", "kobert_confusion_matrix.png");
  footer(s, "오분류 분석은 후속 개선 방향인 문단 앙상블과 계층형 분류로 연결");
}

function slide9() {
  const s = pptx.addSlide(); deckBg(s, 9); label(s, "IMPLEMENTATION"); title(s, "발표에서 보여줄 핵심 코드는 전처리, 실험 통제, Transformer 학습이다.");
  codeBlock(s, 0.9, 1.75, 3.55, 4.55, "preprocess.py", `def normalize_text(value):
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\\S+", " ", text)
    text = re.sub(r"[^0-9A-Za-z가-힣\\s]", " ", text)
    return re.sub(r"\\s+", " ", text).strip()`);
  codeBlock(s, 4.9, 1.75, 3.1, 4.55, "config", `class SplitConfig:
    seed = 42
    train_ratio = 0.70
    valid_ratio = 0.15
    test_ratio = 0.15

min_df = 3
max_df = 0.85`);
  codeBlock(s, 8.45, 1.75, 3.55, 4.55, "train_kobert.py", `tokenizer = AutoTokenizer.from_pretrained(
    "klue/roberta-small"
)
model = AutoModelForSequenceClassification.from_pretrained(
    config.model_name,
    num_labels=len(LABELS)
)
optimizer = torch.optim.AdamW(
    model.parameters(), lr=2e-5
)`);
}

function slide10() {
  const s = pptx.addSlide(); deckBg(s, 10); label(s, "MEDIA"); title(s, "Canva에서는 차트와 코드 캡처를 placeholder에 삽입해 완성도를 높인다.");
  mediaBox(s, 0.85, 1.7, 3.55, 2.15, "성능 비교 차트", "final_macro_f1_comparison.png");
  mediaBox(s, 4.9, 1.7, 3.55, 2.15, "Confusion Matrix", "kobert_confusion_matrix.png");
  mediaBox(s, 8.95, 1.7, 3.55, 2.15, "토큰 비교", "top_tokens_before/after_stopwords.png");
  highlightText(s, [
    { text: "실제 이미지는 Canva에서 직접 삽입한다. ", options: {} },
    { text: "PPT는 구조와 위치를 먼저 고정", options: { bold: true, color: C.accent } },
    { text: "하고, 차트와 코드 캡처는 발표 직전 품질을 확인해 교체한다.", options: {} },
  ], 1.2, 4.8, 9.7, 0.7, 11);
  footer(s, "Replace placeholders with charts, dashboards, code screenshots, or final Canva exports");
}

function slide11() {
  const s = pptx.addSlide(); deckBg(s, 11, true);
  s.addText("THANK YOU", { x: M, y: 0.92, w: 2.3, h: 0.18, fontFace: F.sans, fontSize: 8.2, bold: true, charSpace: 1.5, color: C.gold, margin: 0 });
  s.addText("높은 점수 하나가 아니라,\n왜 그 결과가 나왔는지 설명 가능한 구조를 만들었다.", { x: M, y: 1.65, w: 7.1, h: 1.18, fontFace: F.display, fontSize: 28, bold: true, color: C.white, margin: 0, fit: "shrink" });
  metricCard(s, 0.8, 4.15, 1.85, 1.2, "Final F1", "0.8847", "goal achieved", C.gold);
  metricCard(s, 2.95, 4.15, 1.85, 1.2, "Next", "512", "max_length test", C.gold);
  metricCard(s, 5.1, 4.15, 1.85, 1.2, "Roadmap", "4", "improvement tracks", C.gold);
  const next = [["문단 단위 예측 앙상블", "긴 본문 정보 손실 완화"], ["max_length 256/512", "truncation 영향 검증"], ["KoELECTRA / RoBERTa-base", "한국어 모델 비교 확대"], ["계층형 또는 multi-label", "라벨 경계 혼동 대응"]];
  next.forEach(([h, d], i) => {
    const y = 1.5 + i * 0.88;
    s.addText(String(i + 1).padStart(2, "0"), { x: 8.0, y, w: 0.35, h: 0.18, fontFace: F.sans, fontSize: 8, bold: true, color: C.gold, margin: 0 });
    s.addText(h, { x: 8.5, y: y - 0.02, w: 3.1, h: 0.22, fontFace: F.display, fontSize: 11.5, bold: true, color: C.white, margin: 0, fit: "shrink" });
    s.addText(d, { x: 8.5, y: y + 0.3, w: 3.1, h: 0.18, fontFace: F.sans, fontSize: 7.8, color: "C9DAD7", margin: 0, fit: "shrink" });
  });
  footer(s, "Data Focus · Final NLP project deck", true);
}

[slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8, slide9, slide10, slide11].forEach((fn) => fn());

fs.mkdirSync(path.dirname(OUT), { recursive: true });
pptx.writeFile({ fileName: OUT });
