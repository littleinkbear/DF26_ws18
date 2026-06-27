// =============================================================
// p05 - map() 把資料映射 (mapping) 成視覺屬性
// 教學步驟 5：同一份數值，可以變成不同的「視覺通道 (visual channel)」
//             —— 位置 (position)、大小 (size)、顏色 (color)。
//
// 核心函式：map(value, dataMin, dataMax, screenMin, screenMax)
//   把一個數值 value，從「資料範圍 [dataMin, dataMax]」
//   線性映射 (linear mapping) 到「畫面範圍 [screenMin, screenMax]」。
//
// 線性映射原理（為什麼是「線性」）：
//   先算出 value 在資料範圍裡的比例 (proportion / ratio)：
//       t = (value - dataMin) / (dataMax - dataMin)   // t 介於 0~1
//   再把這個比例套用到畫面範圍：
//       result = screenMin + t * (screenMax - screenMin)
//   map() 內部做的就是這兩步。比例不變，所以是「線性」。
//
// 為什麼一定要先知道資料的 min / max？
//   因為「比例」要有參考兩端。沒有 min/max，就不知道某個數值
//   到底算「小」還是「大」，也就無法決定它該落在畫面的哪裡。
//   本範例用 p5 內建的 min()/max() 從資料自動算出，
//   這樣資料換掉時不用手改範圍（也示範可改成寫死的數值）。
// =============================================================

// ---- 自造資料 (寫死仿真，不讀外部檔) ----
// 想像這是「六個城區」的某項統計值，例如各區的建築平均樓高（單位：層）。
// 同一份 buildingFloors，等一下會被映射成三種不同的視覺屬性。
const buildingFloors = [3, 12, 7, 25, 18, 5];

// 每個區的名稱，純粹用來在畫面上標示，方便對照。
const districtNames = ['A', 'B', 'C', 'D', 'E', 'F'];

// 由資料自動算出最小值 / 最大值。
// dataMin / dataMax 就是 map() 的「資料範圍」兩端。
// （也可以寫死：const dataMin = 0; const dataMax = 30;
//   寫死的好處是基準固定、跨圖可比較；自動算的好處是貼合當前資料。）
let dataMin;
let dataMax;

function setup() {
  createCanvas(720, 520);
  textFont('monospace');

  // min() / max() 接受陣列，回傳其中的最小 / 最大值。
  dataMin = min(buildingFloors);
  dataMax = max(buildingFloors);
}

function draw() {
  background('#f4f4f4');

  drawTitle();

  // 三個區塊，分別示範一種視覺通道。
  drawPositionChannel(60);   // a. 位置 (position)：數值 -> y 座標高低
  drawSizeChannel(220);      // b. 大小 (size)：   數值 -> 圓的直徑
  drawColorChannel(380);     // c. 顏色 (color)：  數值 -> 灰階 / 色相

  noLoop(); // 畫面是靜態的，畫一次就好，省效能。
}

// -------------------------------------------------------------
// a. 位置通道 (position channel)
//    把數值映射成「垂直位置」：數值越大，點畫得越高。
// -------------------------------------------------------------
function drawPositionChannel(baseY) {
  drawSectionLabel(baseY - 18, 'a. 位置 (position)：數值 -> 高低 (y)');

  const rowHeight = 110;            // 這個區塊可用的垂直空間
  const top = baseY + rowHeight;    // 畫面上「低」的 y（值小）
  const bottom = baseY + 10;        // 畫面上「高」的 y（值大）
  const slotWidth = width / buildingFloors.length;

  for (let i = 0; i < buildingFloors.length; i++) {
    const value = buildingFloors[i];
    const x = slotWidth * i + slotWidth / 2;

    // map() 五個參數：
    //   value   = 要映射的數值
    //   dataMin = 資料範圍下限
    //   dataMax = 資料範圍上限
    //   top     = 畫面範圍「對應 dataMin」的一端（這裡放在下方 = 低）
    //   bottom  = 畫面範圍「對應 dataMax」的一端（這裡放在上方 = 高）
    // 注意 top > bottom（y 軸向下為正），所以值大 -> y 小 -> 視覺上更高。
    const y = map(value, dataMin, dataMax, top, bottom);

    stroke(120);
    line(x, top, x, y);            // 一條從基線到資料點的引導線
    noStroke();
    fill('#1f77b4');
    circle(x, y, 14);

    fill(60);
    textAlign(CENTER, TOP);
    text(districtNames[i], x, top + 6);
    textAlign(CENTER, BOTTOM);
    text(value, x, y - 10);
  }
}

// -------------------------------------------------------------
// b. 大小通道 (size channel)
//    把數值映射成「圓的直徑」：數值越大，圓越大。
// -------------------------------------------------------------
function drawSizeChannel(baseY) {
  drawSectionLabel(baseY - 18, 'b. 大小 (size)：數值 -> 直徑 (diameter)');

  const slotWidth = width / buildingFloors.length;
  const centerY = baseY + 70;

  // 直徑的畫面範圍：最小 8px、最大 80px。
  // 注意：用「面積」表示量比用「直徑」更精準，但這裡為教學簡化，
  // 直接把數值線性映射到直徑，先讓學生看懂 map() 改變視覺屬性的概念。
  const minDiameter = 8;
  const maxDiameter = 80;

  for (let i = 0; i < buildingFloors.length; i++) {
    const value = buildingFloors[i];
    const x = slotWidth * i + slotWidth / 2;

    // 同一份數值、同一組 dataMin/dataMax，
    // 只是把畫面範圍換成「直徑」，視覺通道就從位置變成大小。
    const d = map(value, dataMin, dataMax, minDiameter, maxDiameter);

    noStroke();
    fill('#2ca02c');
    circle(x, centerY, d);

    fill(60);
    textAlign(CENTER, TOP);
    text(value, x, centerY + maxDiameter / 2 + 6);
  }
}

// -------------------------------------------------------------
// c. 顏色通道 (color channel)
//    把數值映射成「顏色」。這裡示範兩種常見做法：
//      上排：灰階 (grayscale) —— 把數值映射成亮度 0~255
//      下排：色相 (hue)       —— 搭配 colorMode(HSB) 映射成色相 0~360
// -------------------------------------------------------------
function drawColorChannel(baseY) {
  drawSectionLabel(baseY - 18, 'c. 顏色 (color)：數值 -> 灰階 / 色相 (hue)');

  const slotWidth = width / buildingFloors.length;
  const swatch = 60; // 色塊邊長

  // ---- 上排：灰階 ----
  const grayY = baseY + 6;
  for (let i = 0; i < buildingFloors.length; i++) {
    const value = buildingFloors[i];
    const x = slotWidth * i + slotWidth / 2;

    // 把數值映射成 0(黑) ~ 255(白) 的亮度。
    const gray = map(value, dataMin, dataMax, 0, 255);

    noStroke();
    fill(gray);              // 單一參數的 fill = 灰階亮度
    rectMode(CENTER);
    rect(x, grayY + swatch / 2, swatch, swatch);

    // 文字顏色依底色明暗自動切換，確保看得清楚。
    fill(gray > 128 ? 0 : 255);
    textAlign(CENTER, CENTER);
    text(value, x, grayY + swatch / 2);
  }

  // ---- 下排：色相 (HSB) ----
  const hueY = grayY + swatch + 16;

  // colorMode(HSB, 360, 100, 100)：
  //   把顏色模式 (color mode) 切成 HSB（色相/飽和度/亮度），
  //   並設定色相範圍 0~360、飽和度與亮度範圍 0~100。
  // 這樣就能用 map() 把數值直接算成「色相角度」。
  push();
  colorMode(HSB, 360, 100, 100);
  for (let i = 0; i < buildingFloors.length; i++) {
    const value = buildingFloors[i];
    const x = slotWidth * i + slotWidth / 2;

    // 數值小 -> 色相 210（藍）；數值大 -> 色相 0（紅）。
    // 這是資料視覺化常見的「冷 -> 暖」漸層配色。
    const hue = map(value, dataMin, dataMax, 210, 0);

    noStroke();
    fill(hue, 80, 90);
    rectMode(CENTER);
    rect(x, hueY + swatch / 2, swatch, swatch);

    fill(0, 0, 100); // 在 HSB 下這是白色
    textAlign(CENTER, CENTER);
    text(value, x, hueY + swatch / 2);
  }
  pop(); // 還原成預設 RGB colorMode，不影響其他繪圖
  rectMode(CORNER); // 還原 rectMode
}

// -------------------------------------------------------------
// 輔助：標題與小節標籤
// -------------------------------------------------------------
function drawTitle() {
  noStroke();
  fill(30);
  textAlign(LEFT, TOP);
  textSize(16);
  text('p05  map() 把同一份數值映射成三種視覺通道', 20, 12);
  textSize(11);
  fill(110);
  text('資料：buildingFloors = [' + buildingFloors.join(', ') +
       ']   min=' + dataMin + '  max=' + dataMax, 20, 34);
  textSize(12);
}

function drawSectionLabel(y, label) {
  noStroke();
  fill(70);
  textAlign(LEFT, BOTTOM);
  text(label, 20, y + 12);
}
