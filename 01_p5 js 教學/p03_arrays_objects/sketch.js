// p03 陣列 (array) 與物件 (object)
// 核心觀念：一筆資料 = 一個物件 (object)，多筆資料就放進一個陣列 (array)。
// 本步驟資料全部寫死在程式內 (自造資料)，不讀外部檔；載入外部資料留待下一步。

// ----- 1. 版面相關常數 -----
const CANVAS_W = 720;          // 畫布寬
const CANVAS_H = 480;          // 畫布高
const GROUND_Y = 420;          // 地面基準線 (建築物從這條線往上長)
const BASE_X = 60;             // 第一棟建築的左側起點 X
const GAP = 30;                // 相鄰建築之間的水平間距

// ----- 2. 自造的物件陣列：多棟建築 -----
// 每一個 { } 就是「一筆資料 = 一個物件」，描述一棟建築。
// 屬性 (property)：name 名稱、height 高度(公尺)、area 樓地板面積(平方公尺)。
// 之後我們用 height 決定圖形高度、area 推導圖形寬度，做到「位置/大小由物件屬性決定」。
const buildings = [
  { name: "市政大樓", height: 180, area: 1200 },
  { name: "圖書館",   height: 90,  area: 1600 },
  { name: "車站",     height: 60,  area: 2000 },
  { name: "美術館",   height: 120, area: 900  },
  { name: "住宅塔",   height: 220, area: 700  },
  { name: "商場",     height: 75,  area: 2400 },
];

// ----- 3. (可選) 用 class 示範物件導向寫法 -----
// class 是「物件的設計藍圖」：建構式 constructor 收資料、方法 display() 負責畫自己。
// 把「畫一棟建築」的邏輯包進物件本身，呼叫端只要 b.display() 即可，責任更清楚。
class Building {
  constructor(name, height, area, x) {
    this.name = name;
    this.height = height;     // 公尺，等下會縮放成畫面像素高度
    this.area = area;         // 平方公尺，用來換算長條寬度
    this.x = x;               // 這棟建築在畫面上的左側 X 座標
  }

  // 由面積換算寬度：面積越大畫得越寬 (除以常數只是為了縮放到合理像素)
  get drawW() {
    return this.area / 40;
  }

  // 由高度換算像素高度：除以 0.6 讓最高的塔仍落在畫布內
  get drawH() {
    return this.height / 0.6;
  }

  // 方法 display()：負責把這個物件畫出來 (長條 + 名稱 + 高度標示)
  display() {
    const w = this.drawW;
    const h = this.drawH;
    const topY = GROUND_Y - h;

    // 依高度給不同色相 (hue)，讓視覺上能區分高矮
    const hue = map(this.height, 60, 220, 200, 340);
    colorMode(HSB, 360, 100, 100);
    fill(hue, 55, 85);
    noStroke();
    rect(this.x, topY, w, h, 4); // 圓角長條代表建築量體
    colorMode(RGB, 255);

    // 名稱 (置中於長條下方的地面)
    fill(40);
    textAlign(CENTER, TOP);
    textSize(13);
    text(this.name, this.x + w / 2, GROUND_Y + 6);

    // 高度數值 (標在長條頂端上方)
    textSize(11);
    fill(90);
    text(this.height + " m", this.x + w / 2, topY - 16);
  }
}

// ----- 4. 把資料陣列轉成物件陣列 -----
// 走訪 buildings，依序算出每棟的 X 座標，建立成 Building 實例。
let blocks = [];

function setup() {
  createCanvas(CANVAS_W, CANVAS_H);
  textFont("sans-serif");

  let cursorX = BASE_X; // 目前要擺放的 X 位置，逐棟往右累加
  // forEach 走訪陣列：每一筆物件資料建立一個 Building 並收進 blocks
  buildings.forEach((b) => {
    const block = new Building(b.name, b.height, b.area, cursorX);
    blocks.push(block);
    cursorX += block.drawW + GAP; // 下一棟往右移：本棟寬度 + 間距
  });

  noLoop(); // 此例為靜態圖，畫一次即可，不需持續重繪
}

function draw() {
  background(244);

  // 地面線
  stroke(180);
  line(0, GROUND_Y, width, GROUND_Y);

  // 標題
  noStroke();
  fill(60);
  textAlign(LEFT, TOP);
  textSize(18);
  text("城市建築天際線 (一筆資料 = 一個物件)", BASE_X, 24);

  // 用 for 迴圈走訪物件陣列，請每個物件畫出自己
  for (let i = 0; i < blocks.length; i++) {
    blocks[i].display();
  }
}
