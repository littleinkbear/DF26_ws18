// p02 變數與互動 (variables & interaction)
//
// 本範例要示範三個核心概念：
//   1. 變數 (variable)：用來儲存會隨時間變化的狀態（位置、半徑、顏色等）。
//   2. setup() / draw() 動畫迴圈：
//        - setup() 只在程式啟動時執行「一次」，用來做初始設定。
//        - draw()  會被 p5.js 自動「重複呼叫」，預設約每秒 60 次 (60 fps)，
//          每呼叫一次就是「一幀 (frame)」。把畫面每幀重畫一次，就形成動畫。
//   3. 互動 (interaction)：透過 mouseX / mouseY 取得滑鼠位置讓圖形跟隨，
//        並用事件函式 mousePressed() / keyPressed() 在使用者操作時改變狀態。

// ---- 狀態變數 (state variables) ----
// 這些變數宣告在最外層（全域），所以 setup() 與 draw() 都能存取、修改。
// draw() 每幀讀取並更新它們，畫面就會動起來。

let radius = 60;        // 主圓的半徑，會做「呼吸 (breathing)」效果而變化
let breathPhase = 0;    // 呼吸動畫的相位 (phase)，每幀遞增，丟進 sin() 產生來回變化
let hue = 200;          // 主圓的色相 (hue)，使用 HSB 色彩模式，0~360
let trail = [];         // 滑鼠軌跡：儲存一連串座標點，畫出跟隨滑鼠的尾巴
let dots = [];          // 由使用者點擊產生的固定圓點，示範「加圖形」

// setup() 只跑一次：建立畫布、設定一次性的繪圖參數。
function setup() {
  createCanvas(640, 480);   // 建立 640x480 的畫布 (canvas)
  colorMode(HSB, 360, 100, 100);  // 改用 HSB 色彩模式，方便用 hue 換色
  noStroke();               // 圖形不畫外框線
}

// draw() 每幀重複執行（約 60 fps）：清畫面 -> 更新狀態 -> 重畫。
function draw() {
  background(0, 0, 96);   // 每幀先用淺灰填滿背景，蓋掉上一幀（否則會殘留）

  // --- 動畫：呼吸效果 ---
  // breathPhase 每幀加一點點，sin() 會在 -1~1 之間來回，
  // 因此 radius 會在 (60-20) 到 (60+20) 之間平滑脹縮，像呼吸。
  breathPhase += 0.05;
  radius = 60 + sin(breathPhase) * 20;

  // --- 互動：用 mouseX / mouseY 讓主圓跟隨滑鼠 ---
  // 把目前滑鼠座標存進 trail 陣列，畫出逐漸淡出的軌跡尾巴。
  trail.push({ x: mouseX, y: mouseY });
  if (trail.length > 25) {
    trail.shift();   // 只保留最近 25 個點，舊的丟掉
  }

  // 先畫使用者點擊留下的固定圓點。
  for (const d of dots) {
    fill(d.hue, 70, 90);
    circle(d.x, d.y, 30);
  }

  // 畫滑鼠軌跡：愈舊的點愈小、愈透明。
  for (let i = 0; i < trail.length; i++) {
    const t = trail[i];
    const k = i / trail.length;            // 0(最舊)~1(最新)
    fill(hue, 60, 100, k);                 // 第四個值是透明度 (alpha)
    circle(t.x, t.y, radius * k);
  }

  // 主圓：畫在目前滑鼠位置，半徑隨呼吸變化。
  fill(hue, 80, 95);
  circle(mouseX, mouseY, radius);

  // 在畫面左上角顯示說明文字與目前狀態，方便對照變數的變化。
  fill(0, 0, 30);
  textSize(14);
  text("移動滑鼠：圖形跟隨   點擊：留下圓點   按任意鍵：換色", 12, 24);
  text("frameRate(fps): " + nf(frameRate(), 2, 1) + "   hue: " + int(hue) + "   dots: " + dots.length, 12, 44);
}

// mousePressed()：滑鼠按下時被自動呼叫一次（事件函式 event function）。
// 這裡在點擊位置新增一個固定圓點，示範「用互動改變狀態 / 加圖形」。
function mousePressed() {
  dots.push({ x: mouseX, y: mouseY, hue: random(0, 360) });
}

// keyPressed()：任一鍵按下時被自動呼叫一次。
// 按 'c' 清空所有圓點；其他鍵則隨機換主圓色相，示範「換色」。
function keyPressed() {
  if (key === 'c' || key === 'C') {
    dots = [];        // 清空使用者新增的圖形
  } else {
    hue = random(0, 360);
  }
}
