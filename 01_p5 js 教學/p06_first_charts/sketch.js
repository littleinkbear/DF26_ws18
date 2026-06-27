// =============================================================
// p06 第一個資料圖：長條圖 (bar chart) → 散點圖 (scatter plot) → tooltip
// =============================================================
// 本檔示範如何用 p5.js 把「一份物件陣列資料」畫成圖表。
// 重點觀念：
//   1. 座標軸 (axis) 繪製：螢幕座標系 y 軸往下增加，所以畫圖要做翻轉。
//   2. map() 映射：把資料的數值範圍對應到畫布上的像素範圍。
//   3. 文字標註 (label)：在軸與資料點旁標出名稱與數值。
//   4. tooltip 與 hit-test：用 dist() 計算滑鼠與資料點的距離，
//      距離小於門檻 (threshold) 就判定為「命中」，在滑鼠旁畫提示框。
//
// 資料全部寫死 (hard-coded) 自造，不讀任何外部檔案，可獨立執行。
// 按鍵盤的 1 / 2 可在「長條圖」與「散點圖」兩種檢視 (view) 間切換。
// -------------------------------------------------------------

// ---------- 全域設定 (global config) ----------
const CANVAS_W = 760;   // 畫布寬度
const CANVAS_H = 520;   // 畫布高度

// 繪圖區的邊界留白 (margin)：軸與標籤需要空間
const MARGIN = {
  left: 70,
  right: 40,
  top: 60,
  bottom: 70,
};

// 繪圖內容區 (plot area) 的實際像素範圍，
// 後面 map() 都會把資料映射到這個區間。
const PLOT_LEFT = MARGIN.left;
const PLOT_RIGHT = CANVAS_W - MARGIN.right;
const PLOT_TOP = MARGIN.top;
const PLOT_BOTTOM = CANVAS_H - MARGIN.bottom;

// 目前檢視模式：'bar' 長條圖 或 'scatter' 散點圖
let currentView = 'bar';

// hit-test 命中門檻 (pixel)：滑鼠離資料點多近算「靠近」
const HIT_RADIUS = 14;

// ---------- 自造資料 (hard-coded fake data) ----------
// 每筆是一個物件 (object)：
//   name  區名
//   value 長條圖要用的數值（例如人口或銷售量，單位自訂）
//   x, y  散點圖要用的兩個維度（例如平均所得 vs. 綠地比例）
const data = [
  { name: '中正區', value: 162, x: 78, y: 35 },
  { name: '大同區', value: 128, x: 62, y: 22 },
  { name: '中山區', value: 231, x: 85, y: 41 },
  { name: '松山區', value: 205, x: 90, y: 38 },
  { name: '大安區', value: 312, x: 95, y: 55 },
  { name: '萬華區', value: 188, x: 58, y: 28 },
  { name: '信義區', value: 226, x: 88, y: 60 },
  { name: '士林區', value: 289, x: 70, y: 72 },
];

// ---------- 衍生的資料範圍 (data range) ----------
// map() 需要知道資料的最小/最大值，這裡先算好避免每幀重算。
let valueMax;          // value 的最大值（長條圖 y 軸上限）
let xMin, xMax;        // 散點圖 x 維度範圍
let yMin, yMax;        // 散點圖 y 維度範圍

function setup() {
  createCanvas(CANVAS_W, CANVAS_H);

  // 計算資料範圍。長條圖的高度從 0 起算，所以只需要最大值。
  valueMax = Math.max(...data.map((d) => d.value));

  // 散點圖兩軸各自取 min / max，作為 map() 的來源區間。
  xMin = Math.min(...data.map((d) => d.x));
  xMax = Math.max(...data.map((d) => d.x));
  yMin = Math.min(...data.map((d) => d.y));
  yMax = Math.max(...data.map((d) => d.y));

  textFont('sans-serif');
}

function draw() {
  background(244);

  // 標題與操作提示
  drawHeader();

  // 依目前檢視模式繪製對應圖表。
  // 兩種圖都會在最後處理 tooltip，所以 tooltip 邏輯各自寫在函式裡。
  if (currentView === 'bar') {
    drawBarChart();
  } else {
    drawScatterPlot();
  }
}

// ---------- 標題列 ----------
function drawHeader() {
  noStroke();
  fill(40);
  textAlign(LEFT, TOP);
  textSize(20);
  const title = currentView === 'bar'
    ? '長條圖 Bar Chart：各區數值'
    : '散點圖 Scatter Plot：x 維度 vs. y 維度';
  text(title, MARGIN.left, 16);

  textSize(12);
  fill(120);
  text('按 1 看長條圖 | 按 2 看散點圖 | 滑鼠移到資料點看 tooltip', MARGIN.left, 40);
}

// =============================================================
// 長條圖 (bar chart)
// =============================================================
function drawBarChart() {
  const plotWidth = PLOT_RIGHT - PLOT_LEFT;
  const plotHeight = PLOT_BOTTOM - PLOT_TOP;

  // ---- 1. 畫座標軸 (axis) ----
  // 軸只是兩條線：x 軸在底部，y 軸在左側。
  stroke(80);
  strokeWeight(1);
  line(PLOT_LEFT, PLOT_BOTTOM, PLOT_RIGHT, PLOT_BOTTOM); // x 軸
  line(PLOT_LEFT, PLOT_TOP, PLOT_LEFT, PLOT_BOTTOM);     // y 軸

  // ---- 2. 畫 y 軸刻度與格線 (gridline) ----
  // 把 0..valueMax 分成 5 段，逐段算出像素位置。
  const ticks = 5;
  textSize(11);
  textAlign(RIGHT, CENTER);
  for (let i = 0; i <= ticks; i++) {
    const tickValue = (valueMax / ticks) * i;
    // map() 把資料值映射到像素：注意來源是 0..valueMax，
    // 目標是 PLOT_BOTTOM..PLOT_TOP（底部對應 0、頂部對應最大，y 軸翻轉）。
    const ty = map(tickValue, 0, valueMax, PLOT_BOTTOM, PLOT_TOP);

    // 淡灰格線
    stroke(220);
    line(PLOT_LEFT, ty, PLOT_RIGHT, ty);

    // 刻度文字
    noStroke();
    fill(110);
    text(Math.round(tickValue), PLOT_LEFT - 8, ty);
  }

  // ---- 3. 逐筆畫長條 (bar) ----
  // 每根長條分配等寬的「欄位 (slot)」，長條本身留一點間距。
  const slotWidth = plotWidth / data.length;
  const barWidth = slotWidth * 0.6;

  // 先記錄滑鼠目前命中的那一筆，最後再畫 tooltip（避免被後面的長條蓋住）。
  let hovered = null;

  for (let i = 0; i < data.length; i++) {
    const d = data[i];

    // 長條左上角 x：欄位起點 + 置中留白
    const bx = PLOT_LEFT + slotWidth * i + (slotWidth - barWidth) / 2;

    // 長條高度：map() 把 value 映射成像素高度。
    const barHeight = map(d.value, 0, valueMax, 0, plotHeight);
    const by = PLOT_BOTTOM - barHeight; // 長條頂端 y（往上長）

    // hit-test：滑鼠是否落在這根長條的矩形範圍內？
    // 長條是矩形，所以用「點在矩形內」判定即可（不必用 dist）。
    const isHover =
      mouseX >= bx && mouseX <= bx + barWidth &&
      mouseY >= by && mouseY <= PLOT_BOTTOM;

    // 命中時換成強調色。
    noStroke();
    fill(isHover ? color(231, 111, 81) : color(38, 70, 83));
    rect(bx, by, barWidth, barHeight, 3);

    // x 軸標籤（區名）置於長條下方。
    fill(70);
    textSize(11);
    textAlign(CENTER, TOP);
    text(d.name, bx + barWidth / 2, PLOT_BOTTOM + 6);

    if (isHover) {
      hovered = { d, anchorX: bx + barWidth / 2, anchorY: by };
    }
  }

  // ---- 4. tooltip ----
  if (hovered) {
    drawTooltip(
      `${hovered.d.name}\n數值 value：${hovered.d.value}`,
      mouseX,
      mouseY
    );
  }
}

// =============================================================
// 散點圖 (scatter plot)
// =============================================================
function drawScatterPlot() {
  // ---- 1. 座標軸 ----
  stroke(80);
  strokeWeight(1);
  line(PLOT_LEFT, PLOT_BOTTOM, PLOT_RIGHT, PLOT_BOTTOM); // x 軸
  line(PLOT_LEFT, PLOT_TOP, PLOT_LEFT, PLOT_BOTTOM);     // y 軸

  // 軸名稱 (axis label)
  noStroke();
  fill(90);
  textSize(12);
  textAlign(CENTER, TOP);
  text('x 維度（例如平均所得指數）', (PLOT_LEFT + PLOT_RIGHT) / 2, PLOT_BOTTOM + 36);

  push();
  translate(22, (PLOT_TOP + PLOT_BOTTOM) / 2);
  rotate(-HALF_PI); // 旋轉 90 度讓 y 軸文字直立
  text('y 維度（例如綠地比例）', 0, 0);
  pop();

  // ---- 2. 兩軸刻度 (tick) ----
  textSize(10);
  fill(120);
  const ticks = 4;
  // x 軸刻度
  textAlign(CENTER, TOP);
  for (let i = 0; i <= ticks; i++) {
    const v = map(i, 0, ticks, xMin, xMax);
    const px = map(v, xMin, xMax, PLOT_LEFT, PLOT_RIGHT);
    stroke(225);
    line(px, PLOT_TOP, px, PLOT_BOTTOM);
    noStroke();
    text(Math.round(v), px, PLOT_BOTTOM + 6);
  }
  // y 軸刻度
  textAlign(RIGHT, CENTER);
  for (let i = 0; i <= ticks; i++) {
    const v = map(i, 0, ticks, yMin, yMax);
    // y 軸翻轉：值越大越靠上（PLOT_TOP）。
    const py = map(v, yMin, yMax, PLOT_BOTTOM, PLOT_TOP);
    stroke(225);
    line(PLOT_LEFT, py, PLOT_RIGHT, py);
    noStroke();
    text(Math.round(v), PLOT_LEFT - 8, py);
  }

  // ---- 3. 逐筆畫資料點 (data point) ----
  let hovered = null;

  for (let i = 0; i < data.length; i++) {
    const d = data[i];

    // 把資料的 x, y 兩個維度各自 map() 成像素座標。
    const px = map(d.x, xMin, xMax, PLOT_LEFT, PLOT_RIGHT);
    const py = map(d.y, yMin, yMax, PLOT_BOTTOM, PLOT_TOP); // y 翻轉

    // hit-test：圓點是圓形，用 dist() 算滑鼠到圓心的距離，
    // 小於 HIT_RADIUS 就算命中。這是最典型的「圓形 hit-test」。
    const distance = dist(mouseX, mouseY, px, py);
    const isHover = distance < HIT_RADIUS;

    noStroke();
    fill(isHover ? color(231, 111, 81) : color(42, 157, 143, 200));
    circle(px, py, isHover ? 16 : 11);

    if (isHover) {
      hovered = { d };
    }
  }

  // ---- 4. tooltip ----
  if (hovered) {
    drawTooltip(
      `${hovered.d.name}\nx：${hovered.d.x}　y：${hovered.d.y}`,
      mouseX,
      mouseY
    );
  }
}

// =============================================================
// 通用 tooltip 提示框
// =============================================================
// 參數：
//   msg     要顯示的文字（可含 \n 換行）
//   anchorX, anchorY 提示框要附著的位置（通常是滑鼠座標）
// 作法：先量測文字寬高決定框大小，再用 rect + text 畫出，
//       並做邊界檢查避免框跑出畫布外。
function drawTooltip(msg, anchorX, anchorY) {
  textSize(12);
  textAlign(LEFT, TOP);

  // 量測多行文字的最大寬度與總高度
  const lines = msg.split('\n');
  let maxLineWidth = 0;
  for (const ln of lines) {
    maxLineWidth = Math.max(maxLineWidth, textWidth(ln));
  }
  const padding = 8;
  const lineHeight = 16;
  const boxW = maxLineWidth + padding * 2;
  const boxH = lines.length * lineHeight + padding * 2;

  // 預設畫在滑鼠右下方，偏移一點避免被游標遮住。
  let boxX = anchorX + 14;
  let boxY = anchorY + 14;

  // 邊界檢查：若超出右/下緣，翻到另一側。
  if (boxX + boxW > CANVAS_W) boxX = anchorX - boxW - 14;
  if (boxY + boxH > CANVAS_H) boxY = anchorY - boxH - 14;

  // 提示框背景
  noStroke();
  fill(20, 20, 20, 220);
  rect(boxX, boxY, boxW, boxH, 5);

  // 提示框文字
  fill(255);
  for (let i = 0; i < lines.length; i++) {
    text(lines[i], boxX + padding, boxY + padding + i * lineHeight);
  }
}

// ---------- 鍵盤切換檢視 ----------
function keyPressed() {
  if (key === '1') currentView = 'bar';
  if (key === '2') currentView = 'scatter';
}
