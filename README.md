# Python 基礎與機器學習教學課程

一套以繁體中文撰寫、完全自足的教學教材，涵蓋 Python 基礎、機器學習，以及整合範例。

## 關於本專案

本專案為 **DigitalFUTURES 2026 Workshop 18** 教學教材：

> **台灣陽明交通大學 ｜ 循環城市 AI——利益相關者到城市形態的雙向映射**

工作坊資訊：<https://mp.weixin.qq.com/s/PkTth3sbP-5PDIFz-uRMLQ>

## 專案結構

```
python_basics_course/
├── 00_workflow/            整合範例：用真實資料把多概念串成完整流程
├── 01_py基礎教學/          Python 基礎主課程（12 本 notebook）
├── 02_機器學習教學/        機器學習進階軌（13 本 notebook）
├── requirements.txt        Python 套件鎖定清單（pip freeze）
└── README.md               本檔
```

學習建議順序：先學 `01_py基礎教學` 打底，再進 `02_機器學習教學`；`00_workflow` 是把多概念整合的示範，適合學完基礎後回顧。

---

## 00_workflow — 整合範例

用真實資料、把前面學到的多個概念串成一條完整流程的示範筆記本。三本循序漸進：

| 檔案                       | 主題                                                           |
| -------------------------- | -------------------------------------------------------------- |
| `01_Python_基礎入門.ipynb` | Python 基礎 + 資料處理（import / pandas / numpy / matplotlib） |
| `02_ML_教學.ipynb`         | class / nn.Module / 訓練迴圈                                   |
| `03_PCA_AE_VAE_教學.ipynb` | PCA / AE / VAE 三種壓縮法的概念與視覺化                        |

`_build_notebook.py` 為產生這些範例的輔助腳本。

---

## 01_py基礎教學 — Python 基礎主課程

12 本 notebook，由語法 → 科學運算 → 製圖 → 領域庫，逐步推進。

| #    | 主題                    | #    | 主題                    |
| ---- | ----------------------- | ---- | ----------------------- |
| PY01 | 核心語法                | PY07 | matplotlib 製圖（進階） |
| PY02 | 資料結構與推導式        | PY08 | 物件導向 OOP            |
| PY03 | 函式與程式組織          | PY09 | 例外與檔案 I/O          |
| PY04 | NumPy 數值運算          | PY10 | 命令列 CLI              |
| PY05 | pandas 表格資料         | PY11 | 地理空間與圖論          |
| PY06 | matplotlib 製圖（基礎） | PY12 | Web / API / 文件工具    |

---

## 02\_機器學習教學 — 機器學習進階軌

13 本 notebook（ML00–ML12），從機器學習總覽到生成模型。

| #    | 主題                    | #    | 主題                 |
| ---- | ----------------------- | ---- | -------------------- |
| ML00 | 機器學習總覽            | ML07 | 第一個神經網路 MLP   |
| ML01 | 資料與張量基礎          | ML08 | 訓練的藝術           |
| ML02 | 線性迴歸與梯度下降      | ML09 | CNN 卷積神經網路     |
| ML03 | 邏輯迴歸與分類          | ML10 | Autoencoder 自編碼器 |
| ML04 | PCA 降維                | ML11 | VAE 變分自編碼器     |
| ML05 | KMeans 分群             | ML12 | 進階選修：表徵與生成 |
| ML06 | PyTorch 張量與 autograd |      |                      |

---

## 環境設定

從零開始的完整步驟。所有 notebook 需要 Python 環境與套件。

### 步驟 0：取得專案

二選一：

**A. git clone（建議）**

```bash
git clone https://github.com/ms-112-scott/DF26_ws18.git
cd DF26_ws18
```

> **還沒裝 Git？不用先裝。** 直接雙擊專案根目錄的 `一鍵git更新.bat` 即可——
> 它會自動判斷：沒有 Git 就先幫你純 cmd 安裝（優先用 Windows 內建的 winget），
> 裝好再接著把教材更新到最新版；已經有 Git 就直接更新。
>
> 想自己手動裝也行，開 cmd 一行搞定：
>
> ```cmd
> winget install --id Git.Git -e --source winget
> ```
>
> 裝完**關掉視窗、重開一個新的 cmd**，再執行 `git --version` 確認。
> 若沒有 winget（較舊的 Windows），到 <https://git-scm.com/download/win> 下載安裝即可。

**B. 下載 ZIP**

到 <https://github.com/ms-112-scott/DF26_ws18> →`Code`→`Download ZIP`→解壓縮→進入解壓後的資料夾。

```bash
cd DF26_ws18-master
```

### 步驟 1：檢查 Python

需要 **Python 3.10–3.13**（建議 3.11 或 3.12）。

```bash
# Windows
python --version

# macOS / Linux（多半要用 python3）
python3 --version
```

若無輸出或版本過舊，到 <https://www.python.org/downloads/> 安裝。
Windows 安裝時務必勾選 **Add Python to PATH**。

### 步驟 2：建立並啟用虛擬環境

於專案根目錄（與 `requirements.txt` 同層）執行：

```bash
# 建立 .venv
python -m venv .venv        # macOS / Linux 用 python3
```

```powershell
# 啟用 — Windows PowerShell
.venv\Scripts\Activate.ps1
```

```cmd
:: 啟用 — Windows CMD
.venv\Scripts\activate.bat
```

```bash
# 啟用 — macOS / Linux
source .venv/bin/activate
```

啟用成功後，命令列前方會出現 `(.venv)`。

> PowerShell 若報 `running scripts is disabled`，先執行：
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`，再重新啟用。

確認 Python 來自 `.venv`：

```bash
# Windows
where python
# macOS / Linux
which python3
```

路徑應指向專案內的 `.venv`。

### 步驟 3：安裝套件

```bash
# 先升級 pip
python -m pip install --upgrade pip

# 安裝鎖定清單
pip install -r requirements.txt
```

主要套件：numpy、pandas、matplotlib、scipy、scikit-learn、torch / torchvision、shapely、geopandas、osmnx、networkx、requests、pillow、jupyter。

### 步驟 4：驗證安裝（lib check）

```bash
# 確認套件已裝好（任何一行報錯 = 該套件沒裝成功）
python -c "import numpy, pandas, matplotlib, scipy, sklearn, torch, shapely, geopandas, osmnx, networkx; print('OK，全部套件就緒')"
```

```bash
# 確認版本與重點套件
pip list
python -c "import torch; print('torch', torch.__version__, '｜ CUDA:', torch.cuda.is_available())"
```

看到 `OK，全部套件就緒` 即代表環境完成。

### 步驟 5：開始上課

用 JupyterLab / Jupyter Notebook 或 VS Code 開啟 `.ipynb` 即可逐格執行。

```bash
# 啟動 JupyterLab
jupyter lab
```

VS Code 使用者：開啟 `.ipynb` 後，右上角 Kernel 選擇剛建好的 `.venv`。

> 下次使用前，記得先重新啟用 `.venv`（步驟 2），不必重裝套件。

---

# Python 基础与机器学习教学课程（简体版）

一套以简体中文撰写、完全自足的教学教材，涵盖 Python 基础、机器学习，以及整合范例。

## 关于本项目

本项目为 **DigitalFUTURES 2026 Workshop 18** 教学教材：

> **台湾阳明交通大学 ｜ 循环城市 AI——利益相关者到城市形态的双向映射**

工作坊信息：<https://mp.weixin.qq.com/s/PkTth3sbP-5PDIFz-uRMLQ>

## 项目结构

```
python_basics_course/
├── 00_workflow/            整合范例：用真实数据把多概念串成完整流程
├── 01_py基础教学/          Python 基础主课程（12 本 notebook）
├── 02_机器学习教学/        机器学习进阶轨（13 本 notebook）
├── requirements.txt        Python 包锁定清单（pip freeze）
└── README.md               本档
```

学习建议顺序：先学 `01_py基础教学` 打底，再进 `02_机器学习教学`；`00_workflow` 是把多概念整合的示范，适合学完基础后回顾。

---

## 00_workflow — 整合范例

用真实数据、把前面学到的多个概念串成一条完整流程的示范笔记本。三本循序渐进：

| 文件                       | 主题                                                           |
| -------------------------- | -------------------------------------------------------------- |
| `01_Python_基础入门.ipynb` | Python 基础 + 数据处理（import / pandas / numpy / matplotlib） |
| `02_ML_教学.ipynb`         | class / nn.Module / 训练循环                                   |
| `03_PCA_AE_VAE_教学.ipynb` | PCA / AE / VAE 三种压缩法的概念与可视化                        |

`_build_notebook.py` 为产生这些范例的辅助脚本。

---

## 01_py基础教学 — Python 基础主课程

12 本 notebook，由语法 → 科学运算 → 制图 → 领域库，逐步推进。

| #    | 主题                    | #    | 主题                    |
| ---- | ----------------------- | ---- | ----------------------- |
| PY01 | 核心语法                | PY07 | matplotlib 制图（进阶） |
| PY02 | 数据结构与推导式        | PY08 | 面向对象 OOP            |
| PY03 | 函数与程序组织          | PY09 | 异常与文件 I/O          |
| PY04 | NumPy 数值运算          | PY10 | 命令行 CLI              |
| PY05 | pandas 表格数据         | PY11 | 地理空间与图论          |
| PY06 | matplotlib 制图（基础） | PY12 | Web / API / 文档工具    |

---

## 02\_机器学习教学 — 机器学习进阶轨

13 本 notebook（ML00–ML12），从机器学习总览到生成模型。

| #    | 主题                    | #    | 主题                 |
| ---- | ----------------------- | ---- | -------------------- |
| ML00 | 机器学习总览            | ML07 | 第一个神经网络 MLP   |
| ML01 | 数据与张量基础          | ML08 | 训练的艺术           |
| ML02 | 线性回归与梯度下降      | ML09 | CNN 卷积神经网络     |
| ML03 | 逻辑回归与分类          | ML10 | Autoencoder 自编码器 |
| ML04 | PCA 降维                | ML11 | VAE 变分自编码器     |
| ML05 | KMeans 聚类             | ML12 | 进阶选修：表征与生成 |
| ML06 | PyTorch 张量与 autograd |      |                      |

---

## 环境配置

从零开始的完整步骤。所有 notebook 需要 Python 环境与软件包。

### 步骤 0：获取项目

二选一：

**A. git clone（推荐）**

```bash
git clone https://github.com/ms-112-scott/DF26_ws18.git
cd DF26_ws18
```

> **还没装 Git？不用先装。** 直接双击项目根目录的 `一鍵git更新.bat` 即可——
> 它会自动判断：没有 Git 就先帮你纯 cmd 安装（优先用 Windows 内置的 winget），
> 装好再接着把教材更新到最新版；已经有 Git 就直接更新。
>
> 想自己手动装也行，开 cmd 一行搞定：
>
> ```cmd
> winget install --id Git.Git -e --source winget
> ```
>
> 装完**关掉窗口、重开一个新的 cmd**，再执行 `git --version` 确认。
> 若没有 winget（较旧的 Windows），到 <https://git-scm.com/download/win> 下载安装即可。

**B. 下载 ZIP**

到 <https://github.com/ms-112-scott/DF26_ws18> →`Code`→`Download ZIP`→解压缩→进入解压后的文件夹。

```bash
cd DF26_ws18-master
```

### 步骤 1：检查 Python

需要 **Python 3.10–3.13**（推荐 3.11 或 3.12）。

```bash
# Windows
python --version

# macOS / Linux（多半要用 python3）
python3 --version
```

若无输出或版本过旧，到 <https://www.python.org/downloads/> 安装。
Windows 安装时务必勾选 **Add Python to PATH**。

### 步骤 2：创建并激活虚拟环境

于项目根目录（与 `requirements.txt` 同层）执行：

```bash
# 创建 .venv
python -m venv .venv        # macOS / Linux 用 python3
```

```powershell
# 激活 — Windows PowerShell
.venv\Scripts\Activate.ps1
```

```cmd
:: 激活 — Windows CMD
.venv\Scripts\activate.bat
```

```bash
# 激活 — macOS / Linux
source .venv/bin/activate
```

激活成功后，命令行前方会出现 `(.venv)`。

> PowerShell 若报 `running scripts is disabled`，先执行：
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`，再重新激活。

确认 Python 来自 `.venv`：

```bash
# Windows
where python
# macOS / Linux
which python3
```

路径应指向项目内的 `.venv`。

### 步骤 3：安装软件包

```bash
# 先升级 pip
python -m pip install --upgrade pip

# 安装锁定清单
pip install -r requirements.txt
```

主要软件包：numpy、pandas、matplotlib、scipy、scikit-learn、torch / torchvision、shapely、geopandas、osmnx、networkx、requests、pillow、jupyter。

### 步骤 4：验证安装（lib check）

```bash
# 确认软件包已装好（任何一行报错 = 该包没装成功）
python -c "import numpy, pandas, matplotlib, scipy, sklearn, torch, shapely, geopandas, osmnx, networkx; print('OK，全部软件包就绪')"
```

```bash
# 确认版本与重点软件包
pip list
python -c "import torch; print('torch', torch.__version__, '｜ CUDA:', torch.cuda.is_available())"
```

看到 `OK，全部软件包就绪` 即代表环境完成。

### 步骤 5：开始上课

用 JupyterLab / Jupyter Notebook 或 VS Code 打开 `.ipynb` 即可逐格执行。

```bash
# 启动 JupyterLab
jupyter lab
```

VS Code 用户：打开 `.ipynb` 后，右上角 Kernel 选择刚建好的 `.venv`。

> 下次使用前，记得先重新激活 `.venv`（步骤 2），不必重装软件包。
