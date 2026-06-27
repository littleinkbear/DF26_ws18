# p06 長條圖、散點圖與 tooltip

教學步驟 6：做出你的第一個資料圖 (data visualization)。
從靜態的長條圖 (bar chart) 出發，進到散點圖 (scatter plot)，
最後加上互動式的 tooltip（滑鼠移到資料點時顯示數值）。

## 這一步學什麼

- 把一份「物件陣列 (array of objects)」資料畫成圖表的完整流程。
- 螢幕座標系的陷阱：y 軸往下增加，所以畫圖時要做翻轉 (flip)。
- 用 `map()` 把資料數值映射 (mapping) 到畫布像素位置。
- 用 `dist()` 做命中判定 (hit-test)，實作互動 tooltip。

## 核心概念

### 1. 座標軸繪製 (axis)
座標軸本質上只是兩條線：x 軸在底部、y 軸在左側。
我們先在畫布四周留白 (margin)，圈出一塊「繪圖區 (plot area)」，
所有資料都只畫在這塊區域內，軸與標籤 (label) 畫在留白處。

### 2. map() 映射
`map(value, fromLow, fromHigh, toLow, toHigh)` 把一個數值從來源區間
線性對應到目標區間。例如長條高度：

```js
const barHeight = map(d.value, 0, valueMax, 0, plotHeight);
```

把資料值 `0..valueMax` 對應到像素高度 `0..plotHeight`。
y 軸方向要翻轉時，只要把目標區間反過來寫：
`map(value, 0, valueMax, PLOT_BOTTOM, PLOT_TOP)`，
底部對應最小值、頂部對應最大值。

### 3. 長條圖 vs. 散點圖
- 長條圖：一個類別 (category) 對一個數值，用矩形高度表示大小。
- 散點圖：每筆資料有兩個維度 (x, y)，用圓點的位置表示，
  適合觀察兩個變數之間的關係 (correlation)。

### 4. tooltip 與 hit-test
hit-test（命中判定）就是「判斷滑鼠是否壓在某個圖形上」：

- 長條是矩形，用「點是否落在矩形範圍內」判定
  （比較 `mouseX/mouseY` 與長條的左右上下邊界）。
- 圓點是圓形，用 `dist(mouseX, mouseY, px, py)` 算滑鼠到圓心的距離，
  距離小於門檻 `HIT_RADIUS` 就算命中。

命中時用 `rect()` 畫一個半透明提示框，再用 `text()` 寫上該筆的數值，
並做邊界檢查讓提示框不會跑出畫布。

## 如何執行

這是純前端專案，不需要安裝任何套件。任選一種方式：

1. 直接用瀏覽器開啟 `index.html`（最簡單）。
2. 或在本資料夾啟動一個本機伺服器後用瀏覽器開啟，例如：
   - `python -m http.server 8000`，再開 `http://localhost:8000/`

p5.js 由 CDN 載入（網址寫在 `index.html`），第一次執行需要連網。

## 操作說明

- 滑鼠移到長條或資料點上：旁邊會跳出 tooltip 顯示名稱與數值。
- 按鍵盤 `1`：切換到長條圖檢視 (view)。
- 按鍵盤 `2`：切換到散點圖檢視。

## 可調參數（都在 `sketch.js` 最上方）

- `CANVAS_W` / `CANVAS_H`：畫布尺寸。
- `MARGIN`：四周留白，影響繪圖區大小與軸標籤空間。
- `HIT_RADIUS`：散點圖圓點的命中半徑（像素），越大越容易觸發 tooltip。
- `data`：自造的物件陣列資料。每筆含 `name, value, x, y`，
  可自行增減筆數或改數值，圖表會自動重新計算範圍與布局。

## 檔案

- `index.html`：HTML 模板，載入 p5.js 與 `sketch.js`。
- `sketch.js`：所有繪圖與互動邏輯，資料寫死於檔內、可獨立執行。
- `README.md`：本說明。
