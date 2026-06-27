// p01 畫布與基本圖形
// 主題：Web Editor 上手、畫布座標系 (canvas coordinate system)、
//       基本圖形 (point / line / rect / ellipse)。
//
// p5.js 的兩個核心函式 (function)：
//   setup()：程式啟動時只執行一次，通常用來建立畫布 (canvas) 與初始設定。
//   draw() ：建立畫布後反覆執行 (每秒約 60 次)，用來持續繪製畫面。
// 本範例的畫面是靜態的，所以全部畫完後就用 noLoop() 停掉迴圈，
// 不必每幀重畫，省效能也讓概念更單純。

// 示範用的資料 (data)：座標數值直接寫死 (hard-coded)，不讀任何外部檔案。
// p5.js 的座標單位是像素 (pixel)，整數即可。
const canvasWidth = 640;   // 畫布寬度 width
const canvasHeight = 480;  // 畫布高度 height
const gridStep = 80;       // 格線 (grid line) 間距，每隔 80 像素畫一條輔助線

function setup() {
  // createCanvas(w, h)：建立一塊寬 w、高 h 的畫布。
  // 畫布左上角即為座標系原點 (origin) (0, 0)。
  createCanvas(canvasWidth, canvasHeight);

  // 因為畫面是靜態的，draw() 跑完一次後就停止重複執行。
  noLoop();
}

function draw() {
  background(244);        // 以淺灰色填滿背景，數值 244 是灰階 (greyscale) 亮度
  drawGrid();             // 先畫格線與座標說明，當作底圖
  drawBasicShapes();      // 再畫四種基本圖形疊在上面
}

// 畫出座標系輔助格線並標註原點與軸向。
// 重點在說明：左上角是原點 (0,0)，x 往右遞增、y 往下遞增 (注意 y 向下，
// 和數學課的座標軸方向相反)。
function drawGrid() {
  // 畫淺色格線，方便讀出每個圖形的座標位置。
  stroke(220);            // 線條顏色 (stroke)：淺灰
  strokeWeight(1);        // 線條粗細 (stroke weight)：1 像素

  // 垂直線：x 從 0 到畫布寬，每隔 gridStep 畫一條
  for (let x = 0; x <= canvasWidth; x += gridStep) {
    line(x, 0, x, canvasHeight);
  }
  // 水平線：y 從 0 到畫布高，每隔 gridStep 畫一條
  for (let y = 0; y <= canvasHeight; y += gridStep) {
    line(0, y, canvasWidth, y);
  }

  // 在每條格線交會處標出座標數字 (text)，讓座標系一目了然。
  noStroke();             // 文字不需要外框線
  fill(150);              // 文字填色 (fill)：中灰
  textSize(10);
  for (let x = 0; x <= canvasWidth; x += gridStep) {
    for (let y = 0; y <= canvasHeight; y += gridStep) {
      text(`(${x},${y})`, x + 2, y + 12);
    }
  }

  // 強調原點 (0,0) 在左上角。
  fill(0);
  textSize(14);
  text("原點 origin (0,0)", 6, 36);

  // 用箭頭與文字標出 x 軸 (往右為正) 與 y 軸 (往下為正)。
  stroke(0);
  strokeWeight(2);
  // x 軸方向指示：沿頂端往右
  line(10, 50, 110, 50);
  line(110, 50, 102, 46);
  line(110, 50, 102, 54);
  // y 軸方向指示：沿左側往下
  line(50, 60, 50, 160);
  line(50, 160, 46, 152);
  line(50, 160, 54, 152);

  noStroke();
  fill(0);
  textSize(12);
  text("x 往右 (right) 遞增", 120, 54);
  text("y 往下 (down) 遞增", 60, 120);
}

// 畫出四種基本圖形各至少一個，並在旁邊標註函式名稱與座標意義。
function drawBasicShapes() {
  // 1) point(x, y)：在指定座標畫一個點 (point)。
  //    點預設只有 1 像素，這裡加粗讓它看得見。
  stroke(0);
  strokeWeight(8);
  point(240, 120);        // 點落在 x=240, y=120 的位置
  noStroke();
  fill(0);
  textSize(12);
  text("point(240,120)", 252, 124);

  // 2) line(x1, y1, x2, y2)：從 (x1,y1) 連一條線段 (line) 到 (x2,y2)。
  stroke(30, 100, 200);   // 線條顏色：藍 (R,G,B)
  strokeWeight(3);
  line(240, 160, 480, 240);
  noStroke();
  fill(30, 100, 200);
  text("line(240,160 -> 480,240)", 300, 200);

  // 3) rect(x, y, w, h)：以 (x,y) 為左上角，畫寬 w、高 h 的矩形 (rectangle)。
  //    這裡示範矩形的定位點是左上角，而非中心。
  stroke(0);
  strokeWeight(2);
  fill(240, 180, 60);     // 填色：橘黃
  rect(80, 280, 160, 100);
  noStroke();
  fill(0);
  text("rect(80,280, w160,h100)", 86, 300);

  // 4) ellipse(x, y, w, h)：以 (x,y) 為中心 (center)，畫寬 w、高 h 的橢圓 (ellipse)。
  //    w 等於 h 時就是正圓。注意定位點是中心，和 rect 的左上角不同。
  stroke(0);
  strokeWeight(2);
  fill(200, 80, 120);     // 填色：桃紅
  ellipse(420, 360, 140, 90);
  noStroke();
  fill(255);
  textSize(12);
  textAlign(CENTER);
  text("ellipse 中心(420,360)", 420, 364);
  textAlign(LEFT);        // 還原文字對齊方式，避免影響後續繪製
}
