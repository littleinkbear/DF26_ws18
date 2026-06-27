// p07 進階示範：動畫過場 (animation / transition)、地理資料 (geographic data) 視覺化、聲音頻譜 (FFT)
//
// 本檔完全自足 (self-contained)：所有資料寫死在程式裡，不讀任何外部檔案，
// 因此即使不啟動本地伺服器、用瀏覽器直接開 index.html 也能跑起來 (除了麥克風，見下方說明)。
//
// 三個技術點 (本檔最後皆有對應註解標記)：
//   1. lerp() 動畫過場：在兩組資料狀態之間做線性內插 (linear interpolation)，
//      每一幀只移動一小段，肉眼看到的就是平滑過渡 (transition) 而非瞬間跳變。
//   2. 經緯度 → 像素的 map() 映射：把現實世界的經度 (longitude)、緯度 (latitude)
//      這種「資料範圍」線性對應到「畫布像素範圍」，是所有資料視覺化的核心動作。
//   3. FFT.analyze()：快速傅立葉轉換 (Fast Fourier Transform) 把時域聲音訊號
//      拆解成各頻率的強度陣列，我們再把這個陣列畫成頻譜長條。

// ---------- 全域版面參數 (layout parameters) ----------
const W = 900;            // 畫布寬
const H = 560;            // 畫布高
const PANEL_TOP = 70;     // 上方標題列高度，下面才是內容區

// ---------- 模式切換 (mode) ----------
// 用數字鍵切換目前顯示哪一個示範，避免三個畫面互相干擾。
const MODE_TRANSITION = 1; // 動畫過場
const MODE_GEO = 2;        // 地理資料
const MODE_FFT = 3;        // 聲音頻譜
let mode = MODE_TRANSITION;

// =====================================================================
// 示範一：動畫過場 (transition) 用的資料
// =====================================================================
// 兩組「資料集」(dataset)，每組是一串長條圖的目標高度 (0~1 的比例)。
// 按空白鍵會在 A / B 之間切換目標，長條高度會「漸變」過去而不是瞬間跳。
const datasetA = [0.20, 0.55, 0.80, 0.35, 0.65, 0.45, 0.90, 0.30];
const datasetB = [0.75, 0.25, 0.40, 0.85, 0.30, 0.95, 0.15, 0.60];
let useB = false;                 // 目前目標是不是 B
let currentHeights = [];          // 目前實際顯示的高度 (會被 lerp 慢慢拉向目標)
const LERP_SPEED = 0.08;          // 過場速度：每幀往目標靠近的比例 (越大越快)

// =====================================================================
// 示範二：地理資料 (geographic data) 用的座標點
// =====================================================================
// 自造一組「城市」的經緯度與一個數值 value (例如人口、溫度之類的抽象指標)。
// lat = 緯度 (北正南負)，lon = 經度 (東正西負)。這些是仿真 (mock) 資料，
// 概略對應台灣與東亞幾個城市的位置，重點在示範映射，不追求地理精確。
const cities = [
  { name: 'Taipei',    lat: 25.03, lon: 121.57, value: 95 },
  { name: 'Taichung',  lat: 24.15, lon: 120.68, value: 60 },
  { name: 'Kaohsiung', lat: 22.63, lon: 120.30, value: 72 },
  { name: 'Hualien',   lat: 23.99, lon: 121.60, value: 30 },
  { name: 'Tokyo',     lat: 35.69, lon: 139.69, value: 88 },
  { name: 'Seoul',     lat: 37.57, lon: 126.98, value: 70 },
  { name: 'Shanghai',  lat: 31.23, lon: 121.47, value: 80 },
  { name: 'HongKong',  lat: 22.32, lon: 114.17, value: 50 },
  { name: 'Manila',    lat: 14.60, lon: 120.98, value: 40 },
];

// 這組城市實際落在的經緯度範圍，用來決定 map() 的輸入區間。
// 故意比資料極值再多留一點邊界 (padding)，點才不會貼在畫布邊緣。
const LON_MIN = 112, LON_MAX = 142;   // 經度範圍
const LAT_MIN = 12,  LAT_MAX = 38;    // 緯度範圍

// =====================================================================
// 示範三：聲音頻譜 (FFT) 用的物件
// =====================================================================
// 瀏覽器規定：聲音必須由使用者互動 (例如點一下) 之後才能播放，這叫
// audio context 的「使用者手勢解鎖」(user-gesture unlock)。因此預設不開聲音，
// 按 S 鍵才建立振盪器 (oscillator) 與 FFT，並解鎖 audio context。
let fft;                  // p5.FFT 物件
let osc;                  // p5.Oscillator 物件 (自產聲音，免外部音檔/麥克風)
let audioStarted = false; // 是否已經啟動過聲音

function setup() {
  const cnv = createCanvas(W, H);
  cnv.parent(document.body);
  // 初始化動畫過場的「目前高度」：先設成 datasetA，之後再 lerp 往目標跑。
  currentHeights = datasetA.slice();
  textFont('monospace');
}

function draw() {
  background(244);
  drawHeader();   // 共用的上方標題 / 操作提示

  if (mode === MODE_TRANSITION) {
    drawTransition();
  } else if (mode === MODE_GEO) {
    drawGeo();
  } else if (mode === MODE_FFT) {
    drawFFT();
  }
}

// ---------- 共用標題列 ----------
function drawHeader() {
  noStroke();
  fill(30);
  textSize(20);
  textAlign(LEFT, TOP);
  let title = '';
  if (mode === MODE_TRANSITION) title = '示範 1 / 動畫過場 (lerp transition)';
  if (mode === MODE_GEO)        title = '示範 2 / 地理資料 (map 經緯度映射)';
  if (mode === MODE_FFT)        title = '示範 3 / 聲音頻譜 (FFT 頻譜分析)';
  text(title, 16, 14);

  fill(110);
  textSize(12);
  text('切換示範：[1] 過場  [2] 地理  [3] 頻譜      ' +
       '過場：[空白]換資料集    頻譜：[S]開關聲音', 16, 44);
}

// =====================================================================
// 技術點 1：lerp() 動畫過場 (transition)
// =====================================================================
// 核心觀念：我們不直接把長條畫成「目標高度」，而是維護一個「目前高度」陣列，
// 每一幀都用 lerp(目前, 目標, t) 把目前值往目標值拉近一點點 (t = LERP_SPEED)。
// 因為每幀只走一小步，連續多幀就形成平滑的過場動畫；而且不論何時按鍵切換目標，
// 過場都能從「當下位置」自然接續，不會跳動。
function drawTransition() {
  const target = useB ? datasetB : datasetA;   // 目前要漸變到哪一組
  const n = target.length;
  const areaTop = PANEL_TOP + 30;
  const areaBottom = H - 60;
  const areaH = areaBottom - areaTop;
  const gap = 14;
  const barW = (W - 80 - gap * (n - 1)) / n;

  for (let i = 0; i < n; i++) {
    // lerp(start, stop, amt)：回傳 start 與 stop 之間、比例為 amt 的值。
    // 這裡讓 currentHeights[i] 每幀朝 target[i] 走 LERP_SPEED 的距離。
    currentHeights[i] = lerp(currentHeights[i], target[i], LERP_SPEED);

    const bh = currentHeights[i] * areaH;
    const x = 40 + i * (barW + gap);
    const y = areaBottom - bh;

    // 顏色也隨高度漸變，過場時連顏色一起平滑變化。
    const col = lerpColor(color(80, 160, 220), color(230, 90, 110), currentHeights[i]);
    noStroke();
    fill(col);
    rect(x, y, barW, bh, 6);
  }

  fill(60);
  textSize(13);
  textAlign(CENTER, TOP);
  text('目前目標資料集：' + (useB ? 'B' : 'A') + '（按空白鍵切換，長條會平滑過渡）',
       W / 2, areaBottom + 18);
  textAlign(LEFT, TOP); // 還原對齊設定，避免影響其他畫面
}

// =====================================================================
// 技術點 2：經緯度 → 像素的 map() 映射
// =====================================================================
// map(value, inMin, inMax, outMin, outMax) 把 value 從 [inMin,inMax] 線性
// 對應到 [outMin,outMax]。地圖視覺化的關鍵兩行就是：
//   px = map(lon, LON_MIN, LON_MAX, 左邊界, 右邊界)
//   py = map(lat, LAT_MIN, LAT_MAX, 下邊界, 上邊界)  // 注意 y 要上下顛倒
// 緯度越大代表越北，螢幕上越北 = y 越小，所以 out 區間要反過來寫。
function drawGeo() {
  const padX = 60;
  const padTop = PANEL_TOP + 20;
  const padBottom = H - 30;

  // 畫一個底框代表地圖範圍
  noFill();
  stroke(200);
  rect(padX, padTop, W - padX * 2, padBottom - padTop);

  for (const c of cities) {
    // 經度 → x 像素 (西在左、東在右)
    const px = map(c.lon, LON_MIN, LON_MAX, padX, W - padX);
    // 緯度 → y 像素 (北在上，故 out 區間 padBottom 在前、padTop 在後，達成翻轉)
    const py = map(c.lat, LAT_MIN, LAT_MAX, padBottom, padTop);

    // 點的大小由 value 決定：value 越大點越大
    const d = map(c.value, 0, 100, 6, 34);
    // 點的顏色也由 value 決定：低值偏藍、高值偏紅
    const col = lerpColor(color(60, 140, 230), color(230, 70, 70), c.value / 100);

    noStroke();
    fill(red(col), green(col), blue(col), 200);
    circle(px, py, d);

    // 標上城市名稱
    fill(40);
    textSize(11);
    textAlign(CENTER, TOP);
    text(c.name, px, py + d / 2 + 2);
  }

  textAlign(LEFT, TOP);
  fill(110);
  textSize(12);
  text('點大小與顏色 = value（藍小→紅大）。座標用 map() 由經緯度映射到像素。',
       padX, padBottom + 6);
}

// =====================================================================
// 技術點 3：FFT.analyze() 取頻譜陣列再繪製
// =====================================================================
// fft.analyze() 會回傳一個振幅陣列 (預設長度 1024)，索引代表頻率由低到高，
// 值 0~255 代表該頻率的強度。我們把陣列掃過去畫成一排長條，就是頻譜視覺化。
// 為了避免一開畫面就要求權限，FFT 預設關閉，按 S 鍵才解鎖 audio context 並啟動。
function drawFFT() {
  const areaTop = PANEL_TOP + 30;
  const areaBottom = H - 40;
  const areaH = areaBottom - areaTop;

  if (!audioStarted) {
    fill(60);
    textSize(15);
    textAlign(CENTER, CENTER);
    text('聲音預設關閉。請按 [S] 啟動 audio context 並開始播放振盪器，\n' +
         '即可看到 FFT 頻譜長條。再按一次 [S] 可關閉。',
         W / 2, (areaTop + areaBottom) / 2);
    textAlign(LEFT, TOP);
    return;
  }

  // analyze() 回傳目前這一幀的頻譜陣列 (spectrum)。
  const spectrum = fft.analyze();

  // 只畫前面一段低頻 (人耳對低頻較敏感，也比較好看)，把它鋪滿畫布寬度。
  const bins = 256;
  const barW = (W - 80) / bins;
  noStroke();
  for (let i = 0; i < bins; i++) {
    const amp = spectrum[i];                       // 0~255 的強度
    const bh = map(amp, 0, 255, 0, areaH);         // 強度映射成長條高度
    const x = 40 + i * barW;
    const y = areaBottom - bh;
    const col = lerpColor(color(40, 120, 200), color(250, 210, 60), amp / 255);
    fill(col);
    rect(x, y, barW + 0.5, bh);
  }

  // 慢慢掃動振盪器頻率，讓頻譜長條的「亮點」左右移動，畫面比較有變化。
  const f = map(sin(frameCount * 0.02), -1, 1, 120, 900);
  osc.freq(f);

  fill(60);
  textSize(12);
  text('振盪器頻率：' + nf(f, 0, 0) + ' Hz（自動掃動）。長條 = fft.analyze() 的頻譜強度。',
       40, areaBottom + 12);
}

// ---------- 按鍵控制 ----------
function keyPressed() {
  if (key === '1') mode = MODE_TRANSITION;
  if (key === '2') mode = MODE_GEO;
  if (key === '3') mode = MODE_FFT;

  // 空白鍵：切換動畫過場的目標資料集 (只在過場示範下有意義)
  if (key === ' ') {
    useB = !useB;
  }

  // S 鍵：開關聲音與 FFT。第一次按會解鎖 audio context 並建立物件。
  if (key === 's' || key === 'S') {
    toggleAudio();
  }
}

// 啟動 / 關閉聲音。瀏覽器要求聲音須由使用者手勢觸發，keyPressed 正好是手勢。
function toggleAudio() {
  if (!audioStarted) {
    // userStartAudio() 解鎖 audio context (p5.sound 提供)。
    userStartAudio();

    // 建立一個正弦波振盪器當作聲源，免去外部音檔與麥克風權限。
    osc = new p5.Oscillator('sine');
    osc.amp(0.4);
    osc.freq(440);
    osc.start();

    // 建立 FFT 並接到振盪器；不接的話 analyze() 會分析整體輸出。
    fft = new p5.FFT();
    fft.setInput(osc);

    audioStarted = true;
  } else {
    // 關閉：停止振盪器並標記為未啟動。
    if (osc) osc.stop();
    audioStarted = false;
  }
}
