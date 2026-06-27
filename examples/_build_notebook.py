# -*- coding: utf-8 -*-
# 產生三本教學 notebook（內建 json，不需 nbformat）
#   1) Python_基礎入門.ipynb   純 Python 基礎（讀資料/numpy/畫圖，無 class/torch）
#   2) ML_教學.ipynb           ML 用的 Python：class / nn.Module / torch 訓練迴圈
#   3) PCA_AE_VAE_教學.ipynb   PCA/AE/VAE 概念 + 視覺化（圖像化說明）
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

def mk():
    cells = []
    def md(t): cells.append({"cell_type":"markdown","metadata":{},
                             "source": t.strip("\n").splitlines(keepends=True)})
    def code(t): cells.append({"cell_type":"code","metadata":{},"outputs":[],
                               "execution_count":None,
                               "source": t.strip("\n").splitlines(keepends=True)})
    return cells, md, code

def save(cells, name):
    nb = {"cells": cells,
          "metadata": {"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                       "language_info":{"name":"python","version":"3"}},
          "nbformat":4,"nbformat_minor":5}
    out = os.path.join(HERE, name)
    with open(out,"w",encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print("WROTE", name, "cells=", len(cells))

# 共用：找資料 + 字型 的程式碼字串（三本都要）
SETUP_DATA = """
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 自動找 data 資料夾
CANDS = [
    '../../workshop_build/workshop_build/09_advanced_ml/gan/data',
    'workshop_build/workshop_build/09_advanced_ml/gan/data',
    'data', '../data', '../../gan/data',
]
DATA = None
for guess in CANDS:
    if os.path.exists(os.path.join(guess, 'stakeholder_relations.parquet')):
        DATA = guess; break
print('資料夾：', DATA)

df = pd.read_parquet(os.path.join(DATA, 'stakeholder_relations.parquet'))
print('資料形狀：', df.shape, '(列 = 街區, 欄 = 特徵)')
df.head()
"""

SETUP_FONT = """
# 讓 matplotlib 顯示中文（找不到字型就略過，不影響程式）
from matplotlib import font_manager as fm
for fp in [
    '../../.venv/Lib/site-packages/matplotlib/mpl-data/fonts/ttf/NotoSansCJKsc-Regular.otf',
    '../../../.venv/Lib/site-packages/matplotlib/mpl-data/fonts/ttf/NotoSansCJKsc-Regular.otf',
    'C:/Windows/Fonts/msjh.ttc',
]:
    if os.path.exists(fp):
        try:
            fm.fontManager.addfont(fp)
            plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=fp).get_name()]
            break
        except Exception: pass
plt.rcParams['axes.unicode_minus'] = False
"""

PREP_FEATURES = """
# 選特徵欄 + 標準化（ML 三本都要的前處理）
drop = ['site', 'gx', 'gy']
feat_cols = [c for c in df.columns
             if c not in drop and np.issubdtype(df[c].dtype, np.number)]
X = df[feat_cols].to_numpy(dtype='float32')
mu = X.mean(axis=0); sd = X.std(axis=0); sd[sd < 1e-8] = 1.0
Xs = (X - mu) / sd

share_cols = ['share_state','share_developer','share_resident','share_unknown']
share_idx  = [feat_cols.index(c) for c in share_cols]
names  = ['state 政府','developer 開發商','resident 居民','unknown 未知']
colors = ['#1f77b4','#d62728','#2ca02c','#7f7f7f']
dominant = X[:, share_idx].argmax(axis=1)
print('特徵欄 %d 個，標準化後 Xs =' % len(feat_cols), Xs.shape)
"""

# =========================================================
# 1) Python_基礎入門.ipynb  —— 純基礎（無 class / torch）
# =========================================================
def build_basics():
    cells, md, code = mk()
    md("""
# Python 基礎（第 1 本）：讀資料・算數字・畫圖 🐍

> **目標**：學會三本 ML notebook 開頭都會用到的純 Python 功夫——
> `import`、用 `pandas` 讀表格、用 `numpy` 算數學、用 `matplotlib` 畫圖。
> **不碰** class 和神經網路（那是第 2 本 `ML_教學.ipynb`）。

用法：由上往下，每格 `Shift+Enter`。本書用真實資料示範，整本可執行。

學習路線：
- **第 1 本（本檔）**：Python 基礎 + 資料處理
- 第 2 本 `ML_教學.ipynb`：class / torch / 訓練迴圈
- 第 3 本 `PCA_AE_VAE_教學.ipynb`：三種壓縮法的概念與視覺化
""")
    md("## 0 · 環境自檢")
    code("""
import importlib
for m in ['numpy','pandas','matplotlib']:
    mod = importlib.import_module(m)
    print('OK ', m, mod.__version__)
""")
    md("""
## 1 · `import`：把工具箱搬進來 🔗 三本第 [1] 格

`as np` 是取別名，少打字。`from X import Y` 只拿一個東西。
""")
    code(SETUP_DATA)
    code(SETUP_FONT)
    md("""
**拆解**
- `import numpy as np` / `pandas as pd` / `matplotlib.pyplot as plt`：載入並取別名。
- `os.path.join(a,b)`：安全接路徑。`for...if os.path.exists` 找到資料夾就 `break`。
- `pd.read_parquet(路徑)`：把檔讀成表格 `df`。`df.shape`=(列,欄)。`df.head()` 看前 5 列。
""")
    md("## 2 · 看懂表格 `DataFrame`")
    code("""
print('共', len(df.columns), '欄：')
print(list(df.columns))
print('---')
print('每欄型別：'); print(df.dtypes)
""")
    md("""
## 3 · list 推導式：一行挑出要的欄位 🔗 三本第 [2] 格

```python
feat_cols = [c for c in df.columns if c not in drop and np.issubdtype(df[c].dtype, np.number)]
```
讀法：「對每個欄名 c，若不在 drop 裡且是數字欄，就留下」。
""")
    code("""
# 先看最小例子
nums = [1,2,3,4,5]
print('平方：', [n*n for n in nums])
print('偶數：', [n for n in nums if n % 2 == 0])
""")
    code("""
drop = ['site','gx','gy']
feat_cols = [c for c in df.columns
             if c not in drop and np.issubdtype(df[c].dtype, np.number)]
print('特徵欄 %d 個：' % len(feat_cols)); print(feat_cols)

X = df[feat_cols].to_numpy(dtype='float32')   # 表格 → 純數字陣列
print('X 形狀：', X.shape)
""")
    md("""
## 4 · `numpy` 陣列與標準化 🔗 三本第 [2] 格中段

numpy 讓你「對整個陣列一次運算」。標準化：每欄變平均 0、標準差 1。
```python
mu = X.mean(axis=0)   # 每欄平均
sd = X.std(axis=0)    # 每欄標準差
Xs = (X - mu) / sd    # 廣播：整表一次處理
```
""")
    code("""
mu = X.mean(axis=0)
sd = X.std(axis=0); sd[sd < 1e-8] = 1.0   # 避免除以 0
Xs = (X - mu) / sd
print('標準化後：', Xs.shape)
print('每欄平均≈0：', Xs.mean(axis=0).round(2)[:5], '...')
print('每欄標準差≈1：', Xs.std(axis=0).round(2)[:5], '...')
""")
    md("""
## 5 · 布林遮罩與 `argmax`：圖上顏色哪來的 🔗 三本第 [2] 格結尾

- `argmax(axis=1)`：每列找最大值的位置（0/1/2/3）。
- `dominant == i`：產生一排 True/False，用來只挑某一類。
""")
    code("""
share_cols = ['share_state','share_developer','share_resident','share_unknown']
share_idx  = [feat_cols.index(c) for c in share_cols]
names  = ['state 政府','developer 開發商','resident 居民','unknown 未知']
colors = ['#1f77b4','#d62728','#2ca02c','#7f7f7f']

dominant = X[:, share_idx].argmax(axis=1)
print('前 10 個街區主導者：', dominant[:10])
print('state 主導的街區數：', (dominant == 0).sum())
""")
    md("""
## 6 · `def` 函式：把步驟打包

`def 名字(參數):` → 縮排內容 → `return` 交回結果。
""")
    code("""
def standardize(arr):
    m = arr.mean(axis=0); s = arr.std(axis=0); s[s < 1e-8] = 1.0
    return (arr - m) / s

print('和上面一樣嗎：', np.allclose(Xs, standardize(X)))
""")
    md("""
## 7 · `matplotlib` 畫點圖 🔗 三本核心圖

套路：**for 迴圈，一類一個顏色，疊在同一張圖**。這裡先用最簡單的 PCA 壓成 2 維來畫。
""")
    code("""
from sklearn.decomposition import PCA
Z = PCA(n_components=2).fit_transform(Xs)   # (5438, 2)

plt.figure(figsize=(8,6))
for i in range(4):
    m = (dominant == i)
    plt.scatter(Z[m,0], Z[m,1], s=8, c=colors[i], label=names[i], alpha=0.6)
plt.xlabel('維度 1'); plt.ylabel('維度 2')
plt.title('5438 個街區壓成 2 維')
plt.legend(); plt.grid(alpha=0.3); plt.show()
""")
    md("""
**拆解（三本都一樣）**：`plt.figure()` 開圖 → `for i in range(4)` 四類 → `plt.scatter(x,y,c=,label=)` 畫點 → `plt.legend()`/`plt.show()`。改 `s=`、`alpha=` 看效果。

---
## ✅ 第 1 本完成
你會了：`import` / `pandas` 讀表 / list 推導式 / `numpy` 標準化 / 布林遮罩 / `def` / `matplotlib`。

➡️ **下一步**：打開 **`ML_教學.ipynb`**，學 `class` 和 `torch` 訓練迴圈。
""")
    save(cells, "Python_基礎入門.ipynb")

# =========================================================
# 2) ML_教學.ipynb —— class / nn.Module / torch 訓練迴圈
# =========================================================
def build_ml():
    cells, md, code = mk()
    md("""
# ML 用的 Python（第 2 本）：class・nn.Module・訓練迴圈 🤖

> **前置**：先做完 `Python_基礎入門.ipynb`。
> **目標**：看懂 `2_AE.ipynb` / `3_VAE.ipynb` 裡的**模型定義**和**訓練那一格**。
> 你不用懂背後數學，先學會**讀結構、會跑、會改參數**。

學完這本，三本 notebook 裡剩下唯一沒講過的就只有「數學細節」，程式你全看得懂。
""")
    md("## 0 · 環境 + 載入資料 + 前處理（與第 1 本相同，快速帶過）")
    code("import importlib\nfor m in ['numpy','pandas','matplotlib','sklearn','torch']:\n    print('OK ', m, importlib.import_module(m).__version__ if m!='sklearn' else importlib.import_module('sklearn').__version__)")
    code(SETUP_DATA)
    code(SETUP_FONT)
    code(PREP_FEATURES)
    md("""
## 1 · `class`：自訂一個「型別」

到目前用的都是現成東西（list、DataFrame）。神經網路要**自己定義一個型別**，用 `class`。
先用一個生活化例子看懂 `class` / `__init__` / `self` / 方法。
""")
    code("""
class Dog:
    def __init__(self, name):     # 建構式：造一隻狗時跑一次
        self.name = name          # self = 這隻狗自己，把名字存起來
    def bark(self):               # 方法 = 綁在物件上的函式
        return self.name + ' 汪汪!'

d = Dog('小黑')      # 造一個物件
print(d.name)        # 拿屬性
print(d.bark())      # 呼叫方法
""")
    md("""
**對照神經網路**：`__init__` 裡蓋零件、`forward` 裡定義資料怎麼流過去。下面是 `2_AE.ipynb` 的模型，逐行對照。
""")
    md("""
## 2 · `nn.Module`：神經網路的 class 🔗 2_AE [4]

```python
class AE(nn.Module):          # 繼承 nn.Module（取得訓練所需的全部機制）
    def __init__(self):
        super().__init__()    # 先讓父類別初始化（固定要寫）
        self.enc = nn.Sequential(...)  # encoder 13→2 壓縮
        self.dec = nn.Sequential(...)  # decoder 2→13 還原
    def forward(self, x):     # 資料流過網路
        z = self.enc(x)
        return self.dec(z), z
```
- `nn.Linear(a, b)`：一層全連接，把 a 個數字轉成 b 個。
- `nn.ReLU()`：把負數變 0 的「激活函數」，讓網路能學彎曲。
- `nn.Sequential(...)`：把好幾層串起來，依序通過。
""")
    code("""
import torch
import torch.nn as nn
torch.manual_seed(0)
D = Xs.shape[1]   # 13

class AE(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(D, 32), nn.ReLU(),
            nn.Linear(32, 16), nn.ReLU(),
            nn.Linear(16, 2),
        )
        self.dec = nn.Sequential(
            nn.Linear(2, 16), nn.ReLU(),
            nn.Linear(16, 32), nn.ReLU(),
            nn.Linear(32, D),
        )
    def forward(self, x):
        z = self.enc(x)
        return self.dec(z), z

model = AE()
print(model)
""")
    md("""
## 3 · 訓練迴圈：看懂「訓練」那一格 🔗 2_AE [6]

訓練 = **一個 for 迴圈，重複很多回合，每回合讓誤差小一點**。固定五步：
```python
for epoch in range(80):
    xh, z = model(xt)         # 1 餵資料
    loss  = loss_fn(xh, xt)   # 2 算誤差（還原 vs 原始）
    opt.zero_grad()           # 3 清掉上回梯度
    loss.backward()           # 4 算這回要怎麼調
    opt.step()                # 5 真的調參數
```
""")
    code("""
xt = torch.tensor(Xs)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

history = []
for epoch in range(60):
    xh, z = model(xt)
    loss = loss_fn(xh, xt)
    opt.zero_grad(); loss.backward(); opt.step()
    history.append(loss.item())
    if epoch % 10 == 0:
        print(f'回合 {epoch:3d}   誤差 = {loss.item():.4f}')
print('訓練完成！')
""")
    code("""
# 訓練曲線：往下掉 = 越學越好 🔗 2_AE 圖 1
plt.figure(figsize=(7,4))
plt.plot(history, color='#4C72B0')
plt.xlabel('訓練回合'); plt.ylabel('還原誤差 MSE')
plt.title('AE 訓練曲線'); plt.grid(alpha=0.3); plt.show()
""")
    md("""
## 4 · 用訓練好的模型看結果 🔗 2_AE 圖 2

`model.eval()` + `with torch.no_grad()`：只看結果、不算梯度（比較快）。
""")
    code("""
model.eval()
with torch.no_grad():
    _, Z = model(xt)
Z = Z.numpy()

plt.figure(figsize=(8,6))
for i in range(4):
    m = (dominant == i)
    plt.scatter(Z[m,0], Z[m,1], s=8, c=colors[i], label=names[i], alpha=0.6)
plt.xlabel('latent 1'); plt.ylabel('latent 2')
plt.title('AE 壓出來的 2 維'); plt.legend(); plt.grid(alpha=0.3); plt.show()
""")
    md("""
## 5 · 練習：改參數重跑

回到 §3 把 `range(60)` 改成 `range(150)`，或把 `lr=1e-3` 改成 `1e-2`，再跑一次，
看訓練曲線和點圖怎麼變。**這就是你在三本 notebook 裡會做的事。**

---
## ✅ 第 2 本完成
你會了：`class` / `nn.Module`（`__init__`、`forward`、`self`）/ `nn.Linear`+`ReLU`+`Sequential` / 訓練五步 / `eval()`+`no_grad()`。

➡️ **下一步**：打開 **`PCA_AE_VAE_教學.ipynb`**，搞懂 PCA / AE / VAE 三種壓法**差在哪**（圖像化）。
之後就能完整讀懂 `1_PCA` / `2_AE` / `3_VAE` 三本。
""")
    save(cells, "ML_教學.ipynb")

# =========================================================
# 3) PCA_AE_VAE_教學.ipynb —— 概念 + 視覺化
# =========================================================
def build_pav():
    cells, md, code = mk()
    md("""
# PCA · AE · VAE（第 3 本）：三種壓縮法的概念與視覺化 ✨

> **一句話**：把「**很多數字**」的資料壓成「**2 個數字**」畫成一張圖，
> 但仍能盡量還原。PCA / AE / VAE 是三種壓法，難度與能力遞增。

| | 怎麼壓 | 能彎曲嗎 | 能生成新資料嗎 |
|---|---|---|---|
| **PCA** | 找最分散的直線方向投影 | ❌ 只能直線 | ❌ |
| **AE** | 神經網路自己學壓法 | ✅ 會彎曲 | ❌（latent 有洞） |
| **VAE** | AE + 把 latent 整理整齊 | ✅ | ✅ 可憑空生成 |

本書用**小張玩具資料**先把直覺講清楚（圖像化），最後在真實資料上跑一遍。
對應實作：隔壁 `1_PCA.ipynb` / `2_AE.ipynb` / `3_VAE.ipynb`。
""")
    md("## 0 · 載入 + 工具")
    code(SETUP_DATA)
    code(SETUP_FONT)
    code(PREP_FEATURES)

    # ---- 概念 1: 什麼叫降維 ----
    md("""
## 1 · 直覺：什麼叫「降維」？

想像每個街區有 13 個數字 → 它是 **13 維空間裡的一個點**，看不見。
降維 = 把它**投影**到 2 維紙面，讓我們**看得到**、又盡量不失真。

下圖：把 3 維資料（左）壓成 2 維（右）的示意。
""")
    code("""
# 玩具示意：3 維資料壓成 2 維（純視覺說明）
rng = np.random.default_rng(0)
n = 300
t = rng.normal(size=n)
toy3 = np.stack([t, 0.5*t + 0.3*rng.normal(size=n), -0.8*t + 0.3*rng.normal(size=n)], axis=1)

fig = plt.figure(figsize=(11,4))
ax = fig.add_subplot(1,2,1, projection='3d')
ax.scatter(toy3[:,0], toy3[:,1], toy3[:,2], s=8, c=t, cmap='viridis')
ax.set_title('原始：3 維（難看懂）')
toy2 = PCA(n_components=2).fit_transform(toy3) if False else None  # placeholder
from sklearn.decomposition import PCA
toy2 = PCA(n_components=2).fit_transform(toy3)
ax2 = fig.add_subplot(1,2,2)
ax2.scatter(toy2[:,0], toy2[:,1], s=8, c=t, cmap='viridis')
ax2.set_title('PCA 壓成 2 維（看得懂了）'); ax2.grid(alpha=0.3)
plt.tight_layout(); plt.show()
""")

    # ---- PCA ----
    md("""
## 2 · PCA：找「最分散」的方向 📐

PCA 做的事：在資料裡找一條**讓點散得最開**的直線（PC1），再找第二條垂直的（PC2），
把每個點投影到這兩條線上 → 得到 2 個座標。**只能用直線，不會彎。**

下圖用玩具 2 維資料，畫出 PCA 找到的兩個主方向（箭頭）。
""")
    code("""
from sklearn.decomposition import PCA
# 玩具：一團斜橢圓
pts = rng.normal(size=(400,2)) @ np.array([[2.0,0.8],[0.0,0.6]])
p = PCA(n_components=2).fit(pts)
center = pts.mean(0)

plt.figure(figsize=(6,6))
plt.scatter(pts[:,0], pts[:,1], s=10, alpha=0.4, color='#888')
for k in range(2):
    vec = p.components_[k] * np.sqrt(p.explained_variance_[k]) * 2.5
    plt.arrow(center[0], center[1], vec[0], vec[1], width=0.05,
              color=['#d62728','#1f77b4'][k], length_includes_head=True,
              label=f'PC{k+1}（抓 {p.explained_variance_ratio_[k]*100:.0f}% 資訊）')
plt.legend(); plt.axis('equal'); plt.grid(alpha=0.3)
plt.title('PCA：紅=最分散方向 PC1，藍=次方向 PC2'); plt.show()
""")
    md("""
**重點**：PC1 抓最多資訊，PC2 次之。`explained_variance_ratio_` 告訴你每個方向抓住多少 %。
🔗 對應 `1_PCA.ipynb` 的「圖 2：這 2 個方向抓住多少資訊」。
""")
    code("""
# 真實資料上的 PCA（13 維 → 2 維）🔗 1_PCA 圖 1
pca = PCA(n_components=2); Zp = pca.fit_transform(Xs)
plt.figure(figsize=(7,5.5))
for i in range(4):
    m = (dominant == i)
    plt.scatter(Zp[m,0], Zp[m,1], s=8, c=colors[i], label=names[i], alpha=0.6)
plt.title(f'真實街區 PCA（2 方向共抓 {pca.explained_variance_ratio_.sum()*100:.0f}% 資訊）')
plt.legend(); plt.grid(alpha=0.3); plt.show()
""")

    # ---- AE ----
    md("""
## 3 · AE 自編碼器：讓網路自己學壓法 🌀

PCA 只能直線。**AE** 用神經網路：中間掐一個「**瓶頸**」只有 2 個神經元，
強迫它把 13 個數字擠進 2 個、再還原回 13 個。為了還原得準，那 2 個數字就學成最有用的壓縮。

```
13 維 →[encoder]→ 2 維(瓶頸 latent) →[decoder]→ 13 維
        壓縮                              還原
```
因為中間有 ReLU 會彎，**AE 的 2 維圖通常比 PCA 更會把不同群分開**。
""")
    code("""
# 瓶頸示意圖（畫神經網路形狀，純說明）
import matplotlib.patches as mp
layers = [13,16,2,16,13]; labels=['輸入\\n13','','瓶頸\\n2','','輸出\\n13']
plt.figure(figsize=(9,4)); ax=plt.gca()
for li,(nser) in enumerate(layers):
    xs = li*2.2
    ys = np.linspace(-nser/2, nser/2, nser)
    col = '#d62728' if nser==2 else '#4C72B0'
    ax.scatter([xs]*nser, ys, s=120, color=col, zorder=3)
    if labels[li]: ax.text(xs, max(ys)+1.2, labels[li], ha='center', fontsize=11)
ax.text(2.2,-9,'encoder（壓縮）',ha='center',color='#555')
ax.text(6.6,-9,'decoder（還原）',ha='center',color='#555')
ax.set_title('AE 結構：中間瓶頸只有 2 個 → 被迫學會精華壓縮')
ax.axis('off'); ax.set_ylim(-10,9); plt.show()
""")
    code("""
# 訓練一個小 AE（精簡版）🔗 2_AE
import torch, torch.nn as nn
torch.manual_seed(0); D=Xs.shape[1]
class AE(nn.Module):
    def __init__(s):
        super().__init__()
        s.enc=nn.Sequential(nn.Linear(D,32),nn.ReLU(),nn.Linear(32,16),nn.ReLU(),nn.Linear(16,2))
        s.dec=nn.Sequential(nn.Linear(2,16),nn.ReLU(),nn.Linear(16,32),nn.ReLU(),nn.Linear(32,D))
    def forward(s,x): z=s.enc(x); return s.dec(z), z
ae=AE(); xt=torch.tensor(Xs); opt=torch.optim.Adam(ae.parameters(),1e-3); lf=nn.MSELoss()
for e in range(60):
    xh,z=ae(xt); l=lf(xh,xt); opt.zero_grad(); l.backward(); opt.step()
print('AE 還原誤差：', round(l.item(),4))
ae.eval()
with torch.no_grad(): _,Za=ae(xt)
Za=Za.numpy()
plt.figure(figsize=(7,5.5))
for i in range(4):
    m=(dominant==i); plt.scatter(Za[m,0],Za[m,1],s=8,c=colors[i],label=names[i],alpha=0.6)
plt.title('AE 的 2 維 latent（會彎曲，分群常比 PCA 清楚）')
plt.legend(); plt.grid(alpha=0.3); plt.show()
""")

    # ---- VAE ----
    md("""
## 4 · VAE 變分自編碼器：會「生成」的 AE ✨

AE 的 latent 有很多「洞」——你隨便指一個座標 decode，可能得到垃圾。
**VAE** 多做兩件事，把 latent 整理成一團乾淨的雲（中心在原點）：
1. encoder 不輸出一個點，而是輸出一朵**小雲**（中心 `mu`、大小 `logvar`），從雲裡**抽一點**。
2. 加一個 **KL** 懲罰，逼所有雲都靠近原點、長得規矩。

整理乾淨後 → **隨便從原點附近抽座標 decode，就能生成「像真的但全新」的資料**。
""")
    code("""
# 示意：AE latent（散亂、有洞） vs VAE latent（整齊雲、可取樣）
fig,ax=plt.subplots(1,2,figsize=(10,4.6))
a=rng.normal(size=(200,2))*np.array([3,0.4]); a=a@np.array([[1,1],[0,1]])+np.array([4,4])
ax[0].scatter(a[:,0],a[:,1],s=10,color='#4C72B0'); ax[0].set_title('AE latent：擠一邊、有洞\\n隨便抽點 decode → 可能是垃圾')
ax[0].scatter([0],[0],marker='*',s=200,color='red'); ax[0].annotate('想生成?\\n這裡是洞',(0,0),(-3,-3),color='red')
v=rng.normal(size=(200,2)); ax[1].scatter(v[:,0],v[:,1],s=10,color='#55A868')
ax[1].scatter([0.5],[0.4],marker='*',s=200,color='red'); ax[1].annotate('抽這裡\\ndecode→新資料',(0.5,0.4),(1.4,1.6),color='red')
ax[1].set_title('VAE latent：被 KL 整成原點附近的雲\\n隨便抽 → 生成新資料')
for a_ in ax: a_.grid(alpha=0.3); a_.axis('equal')
plt.tight_layout(); plt.show()
""")
    code("""
# 訓練一個小 VAE 並「生成」新街區 🔗 3_VAE
import torch.nn.functional as F
torch.manual_seed(0)
class VAE(nn.Module):
    def __init__(s):
        super().__init__()
        s.body=nn.Sequential(nn.Linear(D,32),nn.ReLU(),nn.Linear(32,16),nn.ReLU())
        s.mu=nn.Linear(16,2); s.lv=nn.Linear(16,2)
        s.dec=nn.Sequential(nn.Linear(2,16),nn.ReLU(),nn.Linear(16,32),nn.ReLU(),nn.Linear(32,D))
    def enc(s,x): h=s.body(x); return s.mu(h), s.lv(h)
    def forward(s,x):
        m,lv=s.enc(x); z=m+torch.exp(0.5*lv)*torch.randn_like(lv); return s.dec(z),m,lv
v=VAE(); opt=torch.optim.Adam(v.parameters(),1e-3)
for e in range(120):
    xh,m,lv=v(xt); rec=F.mse_loss(xh,xt)
    kl=(-0.5*(1+lv-m**2-lv.exp()).sum(1)).mean(); loss=rec+1.0*kl
    opt.zero_grad(); loss.backward(); opt.step()
print('VAE 還原=%.3f  KL=%.3f'%(rec.item(),kl.item()))

# 生成：從原點附近隨機抽 800 點 decode
v.eval()
with torch.no_grad():
    gen=v.dec(torch.randn(800,2)).numpy()
real2=PCA(n_components=2).fit(Xs); R=real2.transform(Xs); G=real2.transform(gen)
plt.figure(figsize=(7,5.5))
plt.scatter(R[:,0],R[:,1],s=8,c='#bbbbbb',label='真實街區',alpha=0.6)
plt.scatter(G[:,0],G[:,1],s=8,c='#C44E52',label='VAE 生成',alpha=0.5)
plt.title('VAE 生成的新街區(紅) 蓋在真實(灰)上 → 有蓋到才算學會')
plt.legend(); plt.grid(alpha=0.3); plt.show()
""")
    md("""
## 5 · 三兄弟總整理

- **PCA**：最快最簡單，只會直線投影。先用它看資料長相。
- **AE**：會彎曲，壓縮/分群通常更好；但不能生成。
- **VAE**：latent 整齊 → **能生成新資料**，是 GAN/Diffusion 之前最該懂的生成模型基石。

選擇：**只想看 → PCA**；**想壓得更好 → AE**；**想造新資料 → VAE**。

➡️ 概念懂了，回去把隔壁 **`1_PCA` → `2_AE` → `3_VAE`** 三本各跑一遍，
每一行程式你在第 1、2 本都學過了。
""")
    save(cells, "PCA_AE_VAE_教學.ipynb")

build_basics()
build_ml()
build_pav()
print("ALL DONE")
