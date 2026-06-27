# p04 載入外部資料 (Loading External Data)

p5.js 教學步驟 4：用 `loadTable()` / `loadJSON()` 在 `preload()` 載入外部資料。

## 這步學什麼

讓繪圖的內容不再寫死 (hard-coded) 在程式裡，而是從外部檔案（CSV、JSON）讀進來。
資料與程式分離後，換資料就不用改程式碼，這是做資料視覺化 (data visualization) 的基礎。

本範例讀取一份仿真的台灣高樓資料 `buildings.csv`，把每一棟畫成一根水平長條，
長條長度對應樓高 (height)，並標上名稱與樓層數。

## 核心概念

### 1. 非同步載入 (asynchronous loading)

`loadTable()`、`loadJSON()`、`loadImage()` 這類載入函式都是「非同步」的：
呼叫後程式不會原地停下來等檔案下載完，而是先繼續往下跑，等資料到齊才在背景補上。

問題：如果把載入寫在 `setup()`，`setup()` 可能在資料還沒載完時就執行結束了，
這時去取值會拿到 `undefined` 或空表，畫面出錯。

### 2. 為什麼放在 `preload()`

p5.js 對 `preload()` 有特別處理：它會**等 `preload()` 內所有載入工作全部完成**，
才開始執行 `setup()` 與 `draw()`。

因此把 `loadTable()` 放進 `preload()`，就能保證進入 `setup()` 時資料一定已經載完，
不必自己處理回呼 (callback) 或 promise。這是 p5.js 載入外部資源的標準做法。

### 3. `loadTable` 的參數

```js
table = loadTable('buildings.csv', 'csv', 'header');
```

- `'buildings.csv'`：檔案路徑（與 sketch.js 同資料夾）。
- `'csv'`：格式為逗號分隔值 (comma-separated values)。
- `'header'`：宣告第一列是**欄位名稱列 (header row)**，不是資料。
  有了它，就能用欄名（如 `'height'`）取值，且 `getRowCount()` 不會把欄名列算進去。

### 4. p5.Table API（讀表常用方法）

- `table.getRowCount()`：資料列數（用了 `'header'` 時不含欄名列）。
- `table.getString(row, column)`：以**字串**取某格的值，適合顯示文字（如名稱）。
- `table.getNum(row, column)`：以**數值**取某格的值，回傳 number，適合做運算與繪圖。
- `column` 可用欄名字串（`'height'`）或欄位索引（整數）。

> 改用 JSON：若資料是 `data.json`，在 preload() 寫
> `data = loadJSON('data.json');`，得到的是一般 JavaScript 物件／陣列，
> 道理相同 ── 也是因為非同步，所以放在 `preload()`。

## 如何執行

重點：**不要用 `file://` 直接雙擊開啟 `index.html`。**
瀏覽器基於安全性 (CORS, Cross-Origin Resource Sharing) 政策，
通常會擋住用 `file://` 協定載入本地檔案 (`buildings.csv`)，導致 `loadTable` 失敗、畫面空白。
解法是透過一個「本地伺服器」用 `http://` 提供檔案。

### 方法 A：本地伺服器（建議）

在本資料夾 `p04_load_data/` 內開終端機，執行：

```bash
python -m http.server 8000
```

然後在瀏覽器開啟：

```
http://localhost:8000
```

（若系統的 Python 指令是 `python3`，請改用 `python3 -m http.server 8000`。）

### 方法 B：p5 Web Editor（免安裝）

1. 開啟 <https://editor.p5js.org/>
2. 把 `sketch.js` 內容貼進編輯器。
3. 用左側檔案面板的「+」上傳 `buildings.csv`，**務必連同 csv 一起上傳**，
   否則 `loadTable` 找不到檔案。
4. 按 Run 執行。

### 方法 C：VS Code Live Server

安裝 Live Server 擴充套件，對 `index.html` 按右鍵選「Open with Live Server」，
同樣是用 `http://` 提供檔案，可避開 CORS 問題。

## 可調整項

- **換資料**：編輯 `buildings.csv`（或換成你自己的 CSV，欄名對齊即可），程式不用改。
- **改視覺**：在 `sketch.js` 把長條改成圓形、依 `area`（樓地板面積）決定大小、
  或用 `floors`（樓層數）上色。
- **改尺寸**：調整 `createCanvas()` 與版面配置參數（`rowHeight`、`maxBarWidth`）。
- **改格式**：把 `loadTable` 換成 `loadJSON`，搭配對應的 `.json` 資料檔練習。

## 檔案清單

- `index.html` — 載入 p5.js 與 sketch.js 的網頁模板。
- `buildings.csv` — 仿真建築資料（欄位 name, height, floors, area）。
- `sketch.js` — preload 載入 CSV、setup 走訪資料並繪圖，含詳細註解。
- `README.md` — 本說明文件。
