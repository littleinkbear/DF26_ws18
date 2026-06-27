// p04 載入外部資料 (loading external data)
// 教學步驟 4：用 loadTable() 在 preload() 載入外部 CSV 資料。
//
// 核心觀念：
// loadTable() / loadJSON() 都是「非同步」(asynchronous) 函式。
// 非同步的意思是：呼叫後它不會原地等資料下載完，而是「先回頭、之後才完成」。
// 如果在 setup() 裡呼叫，setup() 可能在資料還沒到齊時就跑完了，
// 取值就會拿到 undefined 或空表，畫面出錯。
//
// 解法：放進 preload()。
// p5.js 對 preload() 有特別待遇 ── 它會「等 preload() 裡所有載入工作都完成」，
// 才會去執行 setup() 與 draw()。
// 因此放在 preload() 內就能保證：進到 setup() 時資料一定已經載完。

// 全域變數 table：用來持有載入後的 p5.Table 物件。
// 宣告在最外層，preload() 寫入、setup() 讀取，兩者才能共用。
let table;

function preload() {
  // loadTable(path, type, header)
  //   參數 1 'buildings.csv'：要讀取的檔案路徑（與本檔案同資料夾）。
  //   參數 2 'csv'：檔案格式為逗號分隔值 (comma-separated values)。
  //   參數 3 'header'：宣告「第一列是欄位名稱 (header row)」，
  //                    不是資料列。如此一來就能用欄名（如 'height'）取值，
  //                    且 getRowCount() 不會把欄名那一列算進去。
  //
  // 為什麼寫在 preload()：見檔頭說明 ── 確保 setup() 前資料已載完。
  table = loadTable('buildings.csv', 'csv', 'header');
}

function setup() {
  createCanvas(640, 480);
  background(244);
  textAlign(LEFT, CENTER);

  // getRowCount()：回傳資料列數（因為用了 'header'，不含欄名列）。
  const rowCount = table.getRowCount();

  // 找出最高的建築，作為長條圖的縮放基準 (scale reference)。
  // getNum(row, column)：以「數值」型態取值，回傳 number，方便做運算。
  let maxHeight = 0;
  for (let i = 0; i < rowCount; i++) {
    const h = table.getNum(i, 'height');
    if (h > maxHeight) {
      maxHeight = h;
    }
  }

  // 版面配置參數。
  const marginLeft = 20;
  const marginTop = 30;
  const rowHeight = 50;          // 每一列佔的垂直高度 (pixels)
  const maxBarWidth = 360;       // 最長長條的寬度上限 (pixels)

  // 標題。
  noStroke();
  fill(30);
  textSize(18);
  text('台灣高樓資料視覺化（每列一棟，長條長度 = 樓高）', marginLeft, 15);
  textSize(12);

  // 逐列走訪資料，每一列畫成一根水平長條 + 文字標籤。
  for (let i = 0; i < rowCount; i++) {
    // getString(row, column)：以「字串」型態取值，適合拿來顯示文字（如名稱）。
    const name = table.getString(i, 'name');

    // getNum：拿數值欄位來做計算與繪圖。
    const height = table.getNum(i, 'height');
    const floors = table.getNum(i, 'floors');

    const y = marginTop + i * rowHeight;

    // 依「樓高 / 最高樓高」的比例換算長條寬度，讓最高者佔滿 maxBarWidth。
    const barWidth = map(height, 0, maxHeight, 0, maxBarWidth);

    // 用 HSB 之外的簡單做法：以索引在色相上分布，讓每列顏色不同。
    colorMode(HSB, 360, 100, 100);
    fill((i * 40) % 360, 70, 85);
    noStroke();
    rect(marginLeft, y, barWidth, rowHeight - 16, 6);

    // 文字標籤：名稱、樓高、樓層數。
    colorMode(RGB, 255);
    fill(20);
    text(name + '  ' + height + 'm / ' + floors + 'F',
         marginLeft + barWidth + 8, y + (rowHeight - 16) / 2);
  }
}

// 本範例為靜態圖，資料於 setup() 一次畫完，draw() 不需重繪。
// 保留空 draw() 以符合 p5.js 慣例（也方便日後加入互動）。
function draw() {}
