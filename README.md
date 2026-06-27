# Python 基礎與資料 / 機器學習教學課程

一套以繁體中文撰寫、完全自足的教學教材，涵蓋 Python 基礎、機器學習、p5.js 資料視覺化，以及整合範例。所有教學筆記本與子專案都遵循統一的撰寫與註解規範（見 [`註解原則.md`](註解原則.md)）。

## 專案結構

```
python_basics_course/
├── 00_workflow/            整合範例：用真實資料把多概念串成完整流程
├── 01_p5 js 教學/          p5.js 資料視覺化軌（JavaScript，瀏覽器執行）
├── 02_py基礎教學/          Python 基礎主課程（12 本 notebook）
├── 03_機器學習教學/        機器學習進階軌（13 本 notebook）
├── 註解原則.md             所有教材共用的撰寫 / 註解規範
├── requirements.txt        Python 套件鎖定清單（pip freeze）
└── README.md               本檔
```

學習建議順序：先學 `02_py基礎教學` 打底，再進 `03_機器學習教學`；`01_p5 js 教學` 為獨立軌可隨時進行；`00_workflow` 是把多概念整合的示範，適合學完基礎後回顧。

---

## 00_workflow — 整合範例

用真實資料、把前面學到的多個概念串成一條完整流程的示範筆記本。三本循序漸進：

| 檔案 | 主題 |
|---|---|
| `01_Python_基礎入門.ipynb` | Python 基礎 + 資料處理（import / pandas / numpy / matplotlib） |
| `02_ML_教學.ipynb` | class / nn.Module / 訓練迴圈 |
| `03_PCA_AE_VAE_教學.ipynb` | PCA / AE / VAE 三種壓縮法的概念與視覺化 |

`_build_notebook.py` 為產生這些範例的輔助腳本。

---

## 01_p5 js 教學 — p5.js 資料視覺化

p5.js（Processing 的 JavaScript 版創意程式環境 creative coding）資料視覺化軌，在瀏覽器執行，**不需 Python 環境**。依「畫布基礎 → 互動 → 資料結構 → 載入資料 → 映射 → 圖表 → 進階」循序拆成 7 個可獨立執行的子專案，每個資料夾含 `index.html` + `sketch.js` + `README.md`。

| 子專案 | 主題 |
|---|---|
| `p01_canvas_basics` | 畫布座標系 + 基本圖形（point / line / rect / ellipse） |
| `p02_variables_interaction` | 變數 + setup()／draw() 迴圈 + 滑鼠 / 鍵盤互動 |
| `p03_arrays_objects` | 陣列 array 與物件 object（一筆資料 = 一個物件） |
| `p04_load_data` | `loadTable()` / `loadJSON()` 在 `preload()` 載入外部資料（附 `buildings.csv`） |
| `p05_map_mapping` | `map()` 把數值映射成位置 / 大小 / 顏色 |
| `p06_first_charts` | 長條圖 → 散點圖 → 互動 tooltip |
| `p07_advanced` | 動畫過場 lerp / 聲音 FFT 頻譜 / 地理資料 |

執行方式：
- 直接用瀏覽器開啟子專案內的 `index.html`（首次需連網載入 p5.js CDN）。
- 涉及載入本地檔（`p04`）或音訊（`p07`）的子專案，因瀏覽器 CORS 限制，請改用本地伺服器：在子專案資料夾執行 `python -m http.server 8000`，再開 `http://localhost:8000`；或上傳到 [p5.js Web Editor](https://editor.p5js.org/)。

外部資源整理見 [`01_p5 js 教學/資源收集_p5js資料視覺化.md`](01_p5%20js%20教學/資源收集_p5js資料視覺化.md)。

---

## 02_py基礎教學 — Python 基礎主課程

12 本 notebook，由語法 → 科學運算 → 製圖 → 領域庫，逐步推進。

| # | 主題 | # | 主題 |
|---|---|---|---|
| PY01 | 核心語法 | PY07 | matplotlib 製圖（進階） |
| PY02 | 資料結構與推導式 | PY08 | 物件導向 OOP |
| PY03 | 函式與程式組織 | PY09 | 例外與檔案 I/O |
| PY04 | NumPy 數值運算 | PY10 | 命令列 CLI |
| PY05 | pandas 表格資料 | PY11 | 地理空間與圖論 |
| PY06 | matplotlib 製圖（基礎） | PY12 | Web / API / 文件工具 |

---

## 03_機器學習教學 — 機器學習進階軌

13 本 notebook（ML00–ML12），從機器學習總覽到生成模型。

| # | 主題 | # | 主題 |
|---|---|---|---|
| ML00 | 機器學習總覽 | ML07 | 第一個神經網路 MLP |
| ML01 | 資料與張量基礎 | ML08 | 訓練的藝術 |
| ML02 | 線性迴歸與梯度下降 | ML09 | CNN 卷積神經網路 |
| ML03 | 邏輯迴歸與分類 | ML10 | Autoencoder 自編碼器 |
| ML04 | PCA 降維 | ML11 | VAE 變分自編碼器 |
| ML05 | KMeans 分群 | ML12 | 進階選修：表徵與生成 |
| ML06 | PyTorch 張量與 autograd | | |

---

## 環境設定（Python 軌）

`02_py基礎教學` 與 `03_機器學習教學` 的 notebook 需要 Python 環境與套件。

```bash
# 建立虛擬環境
python -m venv .venv

# 啟用（Windows PowerShell）
.venv\Scripts\Activate.ps1
# 啟用（macOS / Linux）
source .venv/bin/activate

# 安裝套件
pip install -r requirements.txt
```

主要套件：numpy、pandas、matplotlib、scipy、scikit-learn、torch / torchvision、shapely、geopandas、osmnx、networkx、requests、pillow、jupyter。

用 JupyterLab / Jupyter Notebook 或 VS Code 開啟 `.ipynb` 即可逐格執行。

## 撰寫規範

所有教學 notebook 共用 [`註解原則.md`](註解原則.md) 的規範：固定骨架（學習目標 → 概念交替 → 練習 → 小結）、五種純文字註解標記、每概念首見才註、範例自造資料且有輸出、術語首見附英文、無 emoji。
