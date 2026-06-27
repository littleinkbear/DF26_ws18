# p05 — map() 把資料映射 (mapping) 成視覺屬性

教學步驟 5。本步示範資料視覺化 (data visualization) 最關鍵的一個動作：
把「數值」轉換成「能看見的視覺屬性」。負責這件事的靈魂函式就是 `map()`。

## 這一步學什麼

- 認識 `map()` 函式，以及它的五個參數。
- 理解 **線性映射 (linear mapping)**：數值在資料範圍裡的「比例」維持不變，
  只是換到另一個範圍去表現。
- 理解 **視覺通道 (visual channel)**：同一份數值，可以同時變成
  **位置 (position)**、**大小 (size)**、**顏色 (color)**。
- 知道「為什麼要先取得資料的最小值 / 最大值 (min / max)」。

## 核心概念

### 1. `map()`

```
map(value, dataMin, dataMax, screenMin, screenMax)
```

| 參數 | 意義 |
| --- | --- |
| `value` | 要映射的數值（來自資料） |
| `dataMin` | 資料範圍下限 |
| `dataMax` | 資料範圍上限 |
| `screenMin` | 畫面範圍對應 `dataMin` 的一端 |
| `screenMax` | 畫面範圍對應 `dataMax` 的一端 |

內部運算（也就是線性映射的本質）：

```
t      = (value - dataMin) / (dataMax - dataMin)   // 0~1 的比例
result = screenMin + t * (screenMax - screenMin)   // 套回畫面範圍
```

### 2. 為什麼要先知道資料的 min / max

「比例」需要兩端當參考。沒有 min/max，就無法判斷某個數值算大還是算小，
也就無法決定它在畫面上的位置 / 大小 / 顏色。
本範例用 p5 內建的 `min()` 與 `max()` 從資料自動算出，
資料換掉時不必手動改範圍（程式註解也說明了改成寫死數值的差異）。

### 3. 視覺通道 (visual channel)

同一份 `buildingFloors`（各區建築平均樓高，寫死仿真資料）被映射成三種屬性：

- **a. 位置**：數值 -> 垂直高低（`map` 到 y 座標）。
- **b. 大小**：數值 -> 圓的直徑（`map` 到 diameter）。
- **c. 顏色**：數值 -> 灰階亮度（`map` 到 0~255），以及搭配
  `colorMode(HSB)` 把數值 -> 色相 (hue) 做冷暖漸層。

把三種放在同一畫面，能直接看出「同一數值在不同視覺通道下的樣子」。

## 如何執行

此範例完全自足，資料寫死在程式裡，不讀任何外部檔案。

1. 直接用瀏覽器開啟 `index.html` 即可（p5.js 由 CDN 載入）。
2. 若瀏覽器因本機檔案限制無法載入，可在本資料夾啟動簡易伺服器：
   - Python：`python -m http.server`，再開 `http://localhost:8000`
   - VS Code：使用 Live Server 擴充套件

## 可調參數

於 `sketch.js`：

- `buildingFloors`：自造資料陣列，改數值或長度即可看到三種映射同步變化。
- `dataMin` / `dataMax`：預設由 `min()` / `max()` 自動算；可改成寫死（如 0 與 30）
  讓基準固定、跨圖可比較。
- 大小通道的 `minDiameter` / `maxDiameter`：圓直徑的畫面範圍。
- 顏色通道的色相範圍（程式中 `map(value, dataMin, dataMax, 210, 0)`）：
  改兩端角度即可換配色（例如 240 藍 -> 0 紅）。
