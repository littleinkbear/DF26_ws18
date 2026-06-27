# p03 陣列 (array) 與物件 (object)

教學步驟 3：用「一筆資料 = 一個物件」的觀念，把多筆資料放進陣列，再用迴圈把每筆資料畫成圖形。

## 這一步學什麼

- 物件 (object)：用 `{ }` 把一筆資料的多個屬性 (property) 包在一起，例如一棟建築有 `name`、`height`、`area`。
- 陣列 (array)：用 `[ ]` 把多筆資料 (多個物件) 排成一列。
- 走訪 (iterate)：用 `for` 迴圈或 `forEach` 逐一取出每個物件，依屬性決定圖形的位置與大小。
- (可選) 類別 (class)：物件的設計藍圖，含建構式 (constructor) 與方法 (method) `display()`，把「畫自己」的邏輯包進物件，示範物件導向 (OOP) 寫法。

## 核心概念：一筆資料 = 一個物件

一棟建築就是一筆資料，對應一個物件：

```js
{ name: "市政大樓", height: 180, area: 1200 }
```

很多棟建築 = 一個物件陣列：

```js
const buildings = [
  { name: "市政大樓", height: 180, area: 1200 },
  { name: "圖書館",   height: 90,  area: 1600 },
  // ...
];
```

接著走訪陣列，讓每個物件的屬性決定它畫出來的樣子：高度 `height` 換算長條的像素高、面積 `area` 換算寬度。本步驟的資料全部寫死在程式內 (自造資料)，不讀外部檔；載入外部資料留到下一步。

## 如何執行

可在瀏覽器直接執行，需要連線載入 p5.js (使用 CDN)。

- 方法 A：直接用瀏覽器開啟 `index.html`。
- 方法 B (建議)：在本資料夾啟動一個本機伺服器再開啟，避免某些瀏覽器的本機檔案限制。
  - Python：`python -m http.server 8000`，再開 `http://localhost:8000`
  - VS Code：使用 Live Server 擴充套件，對 `index.html` 按右鍵 Open with Live Server

## 檔案說明

- `index.html`：載入 p5.js 與 `sketch.js` 的模板。
- `sketch.js`：自造物件陣列、用 `forEach` 建立 `Building` 物件、用 `for` 迴圈呼叫每個物件的 `display()` 畫出建築天際線。
- `README.md`：本說明。

## 可調參數 (都在 sketch.js 最上方或資料區)

- `CANVAS_W` / `CANVAS_H`：畫布寬高。
- `GROUND_Y`：地面基準線，建築從這條線往上長。
- `BASE_X`：第一棟建築的起始 X。
- `GAP`：相鄰建築之間的水平間距。
- `buildings` 陣列：新增 / 修改 / 刪除其中的物件，立即改變畫面內容；改 `height` 影響長條高度、改 `area` 影響寬度。
- `Building` 類別中的 `drawW`、`drawH`：調整面積與高度換算成像素的縮放比例。
