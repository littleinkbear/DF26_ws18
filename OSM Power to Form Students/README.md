# OSM 权力到形态

看权力如何改写城市天际线。一份动手做的练习：取真实城市建筑，给每栋贴一个角色，切换不同的权力情景（只改高度），观察天际线的变化。

不需要写代码。代码放在 `engine/` 文件夹，不用进去。

## 开始

1. 打开 `城市天际线-动手做.ipynb`（繁体：`城市天際線-動手做.ipynb`）。
2. 菜单 Run，选 Run All Cells，从头到尾运行一遍。
3. 每一步的图会显示在对应格子下面，产物存到 `out/`。

想先看全貌：打开 `图解说明.pptx`。

## 你可以改的地方

要改的设定档就放在这个文件夹里（不在 `engine/` 里），用记事本就能打开：

- `stakeholder_lookup.yaml`：哪种建筑算哪个角色。改完重新运行 **Step 2**。
- `power_scenarios.yaml`：每个角色的高度政策（权重 mult、上限 cap_m、模式 conserve / grow）。改完重新运行 **Step 3 和 Step 4**。
- `config.py`：换城市（进阶）。改中心点 LAT、LON 和半径，默认用离线的大巴窑。

改完要重新运行对应步骤，图才会更新。

## 文件结构

```
OSM Power to Form Students/
├─ 城市天际线-动手做.ipynb / 城市天際線-動手做.ipynb   主练习（简 / 繁）
├─ 进阶-变成3D.ipynb       / 進階-變成3D.ipynb        3D 进阶（简 / 繁）
├─ config.py                  换城市设定（中心点 + 半径，自动推导 BBOX / UTM）
├─ stakeholder_lookup.yaml    谁算谁的（改 → 重跑 Step 2）
├─ power_scenarios.yaml       权力高度政策（改 → 重跑 Step 3、4）
├─ 图解说明.pptx              图解全流程
├─ README.md / STUDENT_NOTES.md
├─ data/                      建筑数据 buildings.csv（离线大巴窑；换地方时自动抓的也存这）
├─ out/                       运行产物：图 PNG / 3D OBJ / CSV
└─ engine/                    程序代码（不用进）
   ├─ common.py               算：载数据 / 贴角色 / 算高度 / 挤 OBJ（model 层，不画图）
   ├─ plots/                  画：每步一个图（data_overview / power_map / policy_heatmap / skyline_panels / metrics / city_3d）
   ├─ geo.py                  换地方前预览座标范围
   ├─ deps.py                 缺套件自动装（osmnx 等）
   ├─ requirements.txt        依赖清单
   └─ steps/                  终端用脚本 step0–step5（可选，与 notebook 共用同一套 plots）
```

分工：`common.py` 只**算**、`plots/` 只**画**、notebook 只**串**（一行调用）。要加新图就在 `plots/` 加一个函数，不动 notebook 结构。

## 依赖

notebook 第一格会自动补装（`deps.ensure()`）。手动装：

```
pip install -r engine/requirements.txt
```

默认大巴窑离线运行，只需 numpy / pandas / matplotlib / pyyaml / shapely。换地方需 osmnx；Step 0 卫星底图需 contextily / pyproj；进阶 3D 的 plotly 旋转视图需 plotly。缺了对应步骤会友好跳过或提示，不影响主流程。

## 边界

高度多为估算（楼层数 × 3.5 米），少数为实测。用途不明的建筑标为 unknown，不做猜测。这是教学练习，不是产权认定，也不是规划预测。
