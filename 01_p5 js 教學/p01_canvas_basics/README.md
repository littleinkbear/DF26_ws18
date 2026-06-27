# p01 畫布與基本圖形 (canvas basics)

p5.js 教學的第一步。目標是熟悉 Web Editor 操作流程，理解畫布座標系
(canvas coordinate system)，並畫出四種最基本的圖形。

## 這一步學什麼

- p5.js 程式的兩個核心函式 (function)：`setup()` 與 `draw()`。
- 畫布 (canvas) 的座標系：原點 (origin) 在哪裡、x 與 y 各往哪個方向遞增。
- 四種基本圖形函式 (drawing function)：`point` / `line` / `rect` / `ellipse`。
- 圖形的定位點差異：矩形 (rectangle) 以左上角定位，橢圓 (ellipse) 以中心 (center) 定位。

## 核心概念

### 1. 畫布座標系 (canvas coordinate system)

- 原點 (0, 0) 在畫布的「左上角」。
- x 座標往「右」遞增 (right)。
- y 座標往「下」遞增 (down)。注意 y 向下為正，和數學課本的座標軸方向相反。
- 單位是像素 (pixel)，整數即可。

範例程式用淺色格線 (grid line) 與座標標籤把這個座標系畫出來，
並用箭頭標出 x、y 兩軸的方向，方便對照每個圖形落在哪裡。

### 2. 基本圖形函式

- `point(x, y)`：在 (x, y) 畫一個點 (point)。預設只有 1 像素，可用 `strokeWeight()` 加粗讓它看得見。
- `line(x1, y1, x2, y2)`：從 (x1, y1) 連一條線段 (line) 到 (x2, y2)。
- `rect(x, y, w, h)`：以 (x, y) 為「左上角」，畫寬 w、高 h 的矩形 (rectangle)。
- `ellipse(x, y, w, h)`：以 (x, y) 為「中心」，畫寬 w、高 h 的橢圓 (ellipse)。w 等於 h 時就是正圓。

輔助設定：

- `createCanvas(w, h)`：建立畫布並決定大小。
- `background(灰階或 R,G,B)`：填滿背景。
- `stroke()` / `strokeWeight()`：設定線條 (stroke) 顏色與粗細。
- `fill()` / `noStroke()`：設定填色 (fill) 與是否畫外框線。
- `noLoop()`：靜態畫面只需畫一次，用它停掉 `draw()` 的重複執行。

## 如何執行

方法一：用瀏覽器直接開啟

1. 用瀏覽器 (Chrome、Edge、Firefox 等) 開啟本資料夾的 `index.html`。
2. `index.html` 會自動從 CDN 載入 p5.js，並引入 `sketch.js`，畫面立即出現。
   (此方法需要可連網，因為 p5.js 由 CDN 載入。)

方法二：用線上 Web Editor

1. 開啟 https://editor.p5js.org/ 。
2. 把 `sketch.js` 的內容貼進編輯器左側的程式區。
3. 按上方的執行 (play) 鈕，右側即顯示畫面。
   (Web Editor 已內建 p5.js，不需要自己引入 CDN。)

## 可調整的參數

全部都在 `sketch.js` 最上方或各圖形的呼叫處：

- `canvasWidth` / `canvasHeight`：畫布大小，改了格線與標籤會跟著重算。
- `gridStep`：格線間距，數值越小格線越密。
- 各圖形函式的座標與大小參數，例如把 `ellipse(420, 360, 140, 90)` 的後兩個數字改成相同值即可得到正圓。
- `fill(...)` / `stroke(...)` 內的數字：單一數字是灰階亮度，三個數字是 R, G, B 顏色。
