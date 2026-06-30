# 上海 · 权力到形态(Shanghai Power to Form)

看权力如何改写城市天际线——这次用**上海本地多源真实数据**(实测高度,陆家嘴最高 **338m**)。
和隔壁 `04_OSM Power to Form Students`(新加坡 / OSM)同一套方法,但更强、也更完整:

- **比 OSM 版强**:① 高度是 **AI 实测**(真超高层 token),不再靠楼层×3.5 估;② unknown 极低(**1–6%**,OSM 版 36%),因为用面状 **EULUC 土地利用**做离散主键;③ **政商可分**(行政办公 vs 商务办公 在用途类别里就分开,OSM tag 做不到)。
- **比 OSM 版完整**:多出**两本讲数据决策的课**(怎么选数据 / 怎么 mapping),以及**进阶的权力算子**——权力不只改高度,而是改**形态语法**。

> 这是 forward 教学练习(改权力 → 看形态),**不是产权认定,也不是规划预测**。零 AI 推断。

---

## 学习路线(4 本 notebook,按顺序)

| # | notebook | 学什么 |
|---|---|---|
| 01 | `01_数据-怎么选与拼接` | 怎么挑数据、5 个来源各司其职、多源空间 join,以及**从下载的数据集亲手建缓存** |
| 02 | `02_映射-谁算谁的` | 离散级联查表:一栋楼怎么对应到**一个**权利方;改表 = 改「谁算谁的」 |
| 03 | `03_城市天际线-动手做` | **主册**:锁死 footprint 与标签,**只调高度**,看权力改写天际线(5 步,接 04 手感) |
| 04 | `04_进阶-权力算子` | **进阶**:9 个原子算子 × 4 种权力体制 → 四种**形态指纹**;复制粘贴换算子 |
| 05 | `05_换地方-按街道取` | **换地方**:研究单位是**街道**(非方框);随包 9 个街道改 `SLUG` 即可切,或按街道名从数据集现建 |

简体为主,每本都附**繁体变体**(同名繁体 `.ipynb`)。

## 你可以改的文件(用记事本就能开,不用进 engine)

- `config.py` —— 换站点 `SLUG`(lujiazui / caoyang / yuyuan);(进阶)填 `DATASET_ROOT` 自己建缓存。
- `shanghai_lookup.yaml` —— 谁算谁的(EULUC→Function→AOI 级联)。改完重跑 **Step 2**。
- `power_scenarios.yaml` —— 只调高度的政策(`mult` / `cap_m` / `_mode`)。改完重跑 **Step 3、4**。
- `regimes.yaml` —— 进阶:9 算子的配方(4 体制)。改完重跑进阶 notebook。
- 想加自己的算子:见 **`算子替换指南.md`** + `engine/my_operator.py`(复制粘贴即可)。

## 跑法

```bash
# 动手:JupyterLab / VS Code 打开 .ipynb,按顺序 Run All
jupyter lab

# 出自含 HTML 报告(繁体:卫星 + 互动 3D + 高度情景 + 进阶算子)
python3 build_report.py            # 三站全套 → out/<slug>/report.html + out/index.html
python3 build_report.py caoyang    # 只跑单站

# (可选)从下载的「上海城市数据集」重建缓存
python3 engine/common.py lujiazui  # 需先在 config.py 设 DATASET_ROOT,见 数据集说明.md
```

## 文件结构

```
05_Shanghai Power to Form Students/
├─ 01_数据-怎么选与拼接.ipynb / .繁    数据:怎么选、怎么拼(含从数据集建缓存)
├─ 02_映射-谁算谁的.ipynb     / .繁    映射:离散级联查表(谁算谁的)
├─ 03_城市天际线-动手做.ipynb / .繁    主册:只调高度,看天际线(5 步)
├─ 04_进阶-权力算子.ipynb     / .繁    进阶:9 算子 × 4 体制 → 形态指纹 + 换算子
├─ 05_换地方-按街道取.ipynb   / .繁    换地方:按街道取(随包 9 街道切换 / 按街道名现建)
├─ config.py                          换站点 / 接数据集(学生主要改这里)
├─ shanghai_lookup.yaml               谁算谁的(改 → 重跑 Step2)
├─ power_scenarios.yaml               只调高度政策(改 → 重跑 Step3、4)
├─ regimes.yaml                       9 算子的配方(进阶)
├─ 算子替换指南.md                    复制粘贴换一个算子
├─ 数据集说明.md                      怎么下载数据集、要哪 5 个文件、DATASET_ROOT 怎么填
├─ build_report.py                    出 out/<slug>/report.html(繁体)
├─ data/<slug>/buildings.parquet      3 站离线缓存(随包带,直接可跑)
├─ out/                               图 / OBJ / CSV / report.html
└─ engine/  (代码,不用进)
   ├─ common.py        算:载缓存 / 建缓存 / 级联贴角色 / 只调高度 / recs 桥 / 挤 OBJ
   ├─ operators.py     9 原子算子 + 配方引擎(进阶)
   ├─ measure.py       形态指纹:FAR/覆盖/高度CV/重心集中/瘦长/细粒
   ├─ my_operator.py   你的算子练习场(模板 + 例子)
   ├─ plots/           画:每步一图 + 算子图谱
   └─ requirements.txt
```

分工:`common.py` 只**算**、`plots/` 只**画**、notebook 只**串**(一行调用)。加新图就在 `plots/` 加一个函数,不动 notebook 结构。

## 数据两条路(详见 `数据集说明.md`)

- **离线(默认)**:随包带 3 站缓存(`data/<slug>/buildings.parquet`),不需联网、不需原始数据集,直接 Run All。
- **自己建(进阶)**:下载「上海城市数据集」、解压、把 `config.DATASET_ROOT` 指过去 → 跑「01_怎么选数据」的建缓存格,从 5 个 spine 文件裁切 + 多源 join 重建缓存。

> 原始数据集体量大、商业授权,**不随包分发**;随包只带 3 站的 parquet 缓存(足够跑全部主流程)。

## 随包 9 个街道(跨三个形态家族)

**3 个代表**(主册/报告默认跑这 3 个):

| slug | 街道 | 家族 | 栋 | 最高 |
|---|---|---|--:|--:|
| `lujiazui` | 陆家嘴街道 | 资本/超高层 | 3263 | **338m** |
| `caoyang` | 曹杨新村街道 | 单位/工人新村 | 1654 | 107m |
| `yuyuan` | 豫园街道 | 居民/里弄石库门 | 1636 | 101m |

**另 6 个也随包**(改 `SLUG` 即可离线切):外滩(资本/金融遗产)· 南京西路(资本/商业)· 控江路 · 彭浦新村(单位/工人新村)· 老西门 · 打浦桥(居民/里弄)。

> 换地方 = 换街道:改 `config.SLUG` 切这 9 个;想要 9 个之外的,按街道名从数据集现建。**完整玩法见 `05_换地方-按街道取` notebook。**

## 诚实边界

- **高度为 AI 实测但有上限**:极端超高层(>~340m)可能低估/缺失,别当测绘。
- **EULUC 为地块(面)级、优先于建筑级 Function**:居住地块内零星公建被并入「居民」。
- **danwei 看不见**:工人新村是国家/单位建的,但用途=居住 → 被算成居民;只有形态记得它是单位建的。
- **informal 本数据无信号 → 恒为空**,不从形态硬猜。
- 进阶算子是**教学假设/可争论的语言**(不含退线/日照/产权/参与),非经验断言。AOI 价格/结构仅作离散 tag、不外发原值。
- **零 AI 推断**:geopandas/shapely/pandas/matplotlib/pyyaml(+ 报告前端 Three.js 着色)。footprint 的「AI解析」是上游数据来源,本 pipeline 不含 AI。
