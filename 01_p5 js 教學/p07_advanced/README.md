# p07 進階：動畫過場 / FFT 頻譜 / 地理資料視覺化

這是 p5.js 教學的第 7 步（進階）。本子專案把三個進階主題收在同一個 sketch 裡，
用數字鍵切換示範，完全自足（self-contained）、不讀任何外部檔案即可執行。

## 這一步學什麼

- **動畫過場（animation / transition）**：用 `lerp()` 讓畫面在兩個狀態之間「平滑漸變」，
  而不是瞬間跳變，是動態資料視覺化最常用的手法。
- **地理資料（geographic data）視覺化**：把現實世界的經緯度（latitude / longitude）
  座標，透過 `map()` 線性映射到畫布像素，畫成點地圖（dot map）。
- **聲音頻譜（FFT, Fast Fourier Transform）**：用 `p5.FFT` 把聲音拆解成各頻率的強度，
  繪製成頻譜長條（spectrum bars）。

## 三個核心概念

### 1. lerp 動畫過場（transition）
`lerp(start, stop, amt)` 回傳介於 `start` 與 `stop` 之間、比例為 `amt`（0~1）的值。
我們維護一組「目前高度」`currentHeights`，每一幀執行
`currentHeights[i] = lerp(currentHeights[i], target[i], LERP_SPEED)`，
讓目前值每幀往目標值靠近一小段。連續多幀就形成平滑過場；
任何時刻切換目標，動畫都會從「當下位置」自然接續。顏色則用 `lerpColor()` 同步漸變。

### 2. 地理座標映射（map）
`map(value, inMin, inMax, outMin, outMax)` 把一個數值從輸入區間線性對應到輸出區間。
畫地圖的關鍵兩行：
```
px = map(lon, LON_MIN, LON_MAX, 左邊界, 右邊界);
py = map(lat, LAT_MIN, LAT_MAX, 下邊界, 上邊界);  // y 要上下顛倒
```
緯度越大代表越北，而螢幕上越北 = y 越小，所以輸出區間要把「下邊界」寫在前面達成翻轉。
點的大小與顏色另外用 `map()` / `lerpColor()` 由 `value` 決定。

### 3. FFT 頻譜
`fft.analyze()` 回傳一個振幅陣列（預設長度 1024），索引代表頻率由低到高，
值為 0~255 的強度。把陣列掃過去、用 `map()` 把強度轉成長條高度逐一畫出，就是頻譜視覺化。
本示範用 `p5.Oscillator`（振盪器）自產正弦波當聲源，所以不需要外部音檔，也不需要麥克風。

## 如何執行

1. **最簡單**：直接用瀏覽器打開 `index.html`。動畫過場與地理資料兩項可立即運作。
2. **聲音（FFT）需要使用者手勢解鎖**：瀏覽器規定 audio context 必須由互動觸發，
   所以聲音預設關閉。切到示範 3 後按 **S** 鍵才會啟動 `userStartAudio()` 並播放振盪器。
3. **建議用本地伺服器**：部分瀏覽器對 `file://` 協定下的 p5.sound 有限制。
   若聲音無法啟動，請在本資料夾開一個本地伺服器再用 `http://localhost` 開啟，例如：
   - Python：`python -m http.server 8000`，然後瀏覽 `http://localhost:8000`
   - VS Code：使用 Live Server 擴充套件
4. p5.js 與 p5.sound 由 `index.html` 透過 CDN 載入，需要網路連線。

> 關於麥克風：本示範刻意改用振盪器示範，避免一開啟就跳出權限請求。
> 若想改成麥克風輸入，可在程式中建立 `let mic = new p5.AudioIn(); mic.start();`
> 並改用 `fft.setInput(mic)`；這會在啟動時要求麥克風（microphone）權限。

## 操作說明（按鍵）

| 按鍵    | 作用                                            |
| ------- | ----------------------------------------------- |
| `1`     | 切到示範 1：動畫過場                             |
| `2`     | 切到示範 2：地理資料                             |
| `3`     | 切到示範 3：聲音頻譜                             |
| `空白`  | （示範 1）在資料集 A / B 之間切換目標，觸發過場  |
| `S`     | （示範 3）開 / 關聲音與 FFT；第一次按會解鎖音訊  |

## 可調參數

於 `sketch.js` 上方：

- `LERP_SPEED`：過場速度。越大過渡越快、越小越慢越柔。
- `datasetA` / `datasetB`：兩組長條目標高度（0~1），可自行增減元素。
- `cities`：地理資料陣列，每筆 `{ name, lat, lon, value }`，可加入自己的城市。
- `LON_MIN/LON_MAX`、`LAT_MIN/LAT_MAX`：地圖經緯度範圍（影響 map 映射與留白）。
- `drawFFT()` 內的 `bins`：頻譜顯示的頻率段數（畫前段低頻較好看）。
- `osc.amp(...)` 與頻率掃動公式：調整音量與頻譜亮點移動的範圍。

## 延伸方向

- **過場**：改用 `lerp` 同時內插座標位置，做出點在兩種佈局間「飛行」的動畫；
  或加入緩動函數（easing）讓過場有加速度感。
- **地理**：改用真實的 GeoJSON 資料與地圖投影（projection，例如 Mercator）；
  用 value 做熱力圖（heatmap）或加上滑鼠 hover 顯示細節（tooltip）。
- **FFT**：改用麥克風輸入做即時頻譜；用 `fft.getEnergy('bass')` 取特定頻段能量
  驅動視覺；或用 `fft.waveform()` 畫時域波形（waveform）。
