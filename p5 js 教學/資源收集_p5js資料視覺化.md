# p5.js 資料視覺化 — 資源收集

p5.js 是 Processing 的 JavaScript 版創意程式環境 creative coding，跑在瀏覽器、適合藝術 / 設計 / 教育與初學者。
本檔收集「資料視覺化 data visualization」相關的官方資源、教學課程與作品範例，作為教學備課起點。

> 說明：以下皆為外部連結（2026-06 經網路搜尋確認）。實際教學前建議再點開確認內容仍在線。

---

## 1. 官方核心資源（必看）

| 資源 | 用途 | 連結 |
|---|---|---|
| p5.js 官方範例 Examples | 短小範例，含色彩、碎形、數學視覺化 | https://p5js.org/examples/ |
| p5.js 官方教學 Tutorials | 從零開始的逐步課程（變數、條件、互動、陣列、物件） | https://p5js.org/tutorials/ |
| p5.js Reference | API 查詢（函式說明 + 可跑範例） | https://p5js.org/reference/ |
| p5.js Web Editor | 線上免安裝寫 / 跑 / 分享 sketch | https://editor.p5js.org/ |
| p5.js Showcase | 國際社群創作作品集（找靈感主力） | https://showcase.p5js.org/ |

## 2. 資料載入 API（資料視覺化的關鍵）

資料視覺化第一步是「把資料讀進來」。p5.js 核心函式：

| 函式 | 說明 | 連結 |
|---|---|---|
| `loadTable()` | 讀 CSV / 表格成 p5.Table；需放 preload() 確保載完才畫 | https://p5js.org/reference/p5/loadTable/ |
| Table 範例 | 官方範例：從 CSV 載入泡泡資料（改自 Shiffman 的 Processing 範例） | https://p5js.org/examples/loading-and-saving-data-table/ |
| Advanced Data: Load Saved JSON | Coding Train 在 Web Editor 的 JSON 載入示範 | https://editor.p5js.org/codingtrain/sketches/zFsolg5ZJ |

重點觀念：`loadTable`/`loadJSON` 是非同步 asynchronous，放在 `preload()` 內可保證 `setup()`／`draw()` 前載入完成。

## 3. 系統化教學課程

| 課程 | 程度 | 連結 |
|---|---|---|
| The Coding Train — Code! Programming with p5.js | 初學者 7 小時完整入門（Daniel Shiffman，影片） | https://thecodingtrain.com/tracks/code-programming-with-p5-js/ |
| The Coding Train — Tracks 總覽 | 各主題軌（含 data / API 進階） | https://thecodingtrain.com/tracks/ |
| Shiffman — Data and APIs (A2Z) | fetch、API、JSON 等資料處理進階 | https://shiffman.net/a2z/data-apis/ |
| Codecademy — Learn p5.js | 互動式入門（動態視覺、生成設計） | https://www.codecademy.com/learn/learn-p5js |
| Happy Coding — p5.js Tutorials | 文字教學，循序漸進 | https://happycoding.io/tutorials/p5js/ |
| Kadenze — Intro to Programming for Visual Arts with p5.js | 視覺藝術導向課程 | https://www.kadenze.com/courses/introduction-to-programming-for-the-visual-arts-with-p5-js/info |
| Class Central — p5.js 課程彙整 | 90+ 免費 / 付費課程清單 | https://www.classcentral.com/subject/p5 |

## 4. 資料視覺化教學文章 / 範例作品

| 資源 | 內容 | 連結 |
|---|---|---|
| Creative Bloq — Explore data visualisation with p5.js | 入門教學文（含聲音 FFT 資料視覺化） | https://www.creativebloq.com/how-to/data-visualisation-with-p5js |
| teaching.alptugan.com — P5JS Data Visualization | 教學單元（課堂用） | https://teaching.alptugan.com/Tutorials/P5JS---Data-Visualization |
| VDA-Lab — Hands-on data visualization using p5 | 實作工作坊講義 | https://vda-lab.github.io/2015/10/hands-on-data-visualization-using-p5 |
| Medium（Levente Simon）— 用 p5.js 5 步驟畫河流 | ChatGPT + p5.js 地理資料視覺化案例 | https://medium.com/@simon.levente/data-visualisation-p5js-and-chatgpt-highlighting-rivers-in-5-steps-162b28f103d5 |
| Web Editor — data visualization class example（isob） | 課堂範例 sketch | https://editor.p5js.org/isob/sketches/n_Spb0t6e |
| Web Editor — Project 2 Data Visualization（denaplesk2） | 學生作品 sketch | https://editor.p5js.org/denaplesk2/sketches/HJ9FsAmyG |
| Web Editor — Data-Visualization（bavazzanos1） | 社群作品 sketch | https://editor.p5js.org/bavazzanos1/sketches/rk9nXIGyz |
| CodePen — p5.js data visualization（enginarslan） | 可即看即改的範例 | https://codepen.io/enginarslan/pen/aJJmZP |
| Pinterest — p5.js 資料設計靈感板 | 100+ 視覺靈感 | https://www.pinterest.com/danielfeusse/p5js/ |

## 5. 建議教學切入順序（草稿）

1. Web Editor 上手 + 畫布座標系 → 畫基本圖形（point / line / rect / ellipse）
2. 變數、`setup()`／`draw()` 迴圈、互動（滑鼠 / 鍵盤）
3. 陣列 array 與物件 object（一筆資料 = 一個物件）
4. `loadTable` / `loadJSON` 載入外部資料（放 `preload()`）
5. 把資料映射 map 成視覺屬性：位置、大小、顏色（`map()` 函式是核心）
6. 做出第一個圖：長條圖 → 散點圖 → 互動 tooltip
7. 進階：動畫過場、聲音 FFT、地理資料

> map() 把數值從資料範圍線性映射到畫面範圍（如數值→像素高度 / 顏色），是資料視覺化的靈魂函式。

---

Sources（搜尋來源）:
- [p5.js Examples](https://p5js.org/examples/)
- [p5.js Tutorials](https://p5js.org/tutorials/)
- [p5.js Showcase](https://showcase.p5js.org/)
- [loadTable reference](https://p5js.org/reference/p5/loadTable/)
- [Table example](https://p5js.org/examples/loading-and-saving-data-table/)
- [The Coding Train — p5.js](https://thecodingtrain.com/tracks/code-programming-with-p5-js/)
- [Shiffman Data and APIs](https://shiffman.net/a2z/data-apis/)
- [Codecademy Learn p5.js](https://www.codecademy.com/learn/learn-p5js)
- [Happy Coding p5.js](https://happycoding.io/tutorials/p5js/)
- [Creative Bloq data viz with p5.js](https://www.creativebloq.com/how-to/data-visualisation-with-p5js)
- [alptugan teaching](https://teaching.alptugan.com/Tutorials/P5JS---Data-Visualization)
- [VDA-Lab hands-on](https://vda-lab.github.io/2015/10/hands-on-data-visualization-using-p5)
- [Class Central p5 courses](https://www.classcentral.com/subject/p5)
