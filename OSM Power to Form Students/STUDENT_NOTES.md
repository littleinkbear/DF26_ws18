# 速查

## 一句话
真实建筑 → 贴角色 → 切权力情景（只改高度）→ 看天际线。

## 能改的文件（就在这个文件夹，不用进 engine）
- `stakeholder_lookup.yaml`：哪种建筑算哪个角色。改完重跑 Step 2。
- `power_scenarios.yaml`：每个角色怎么调高度。改完重跑 Step 3、Step 4。
- `config.py`：换城市（进阶）。

## 产物在哪
- `out/`：所有图 PNG、3D 的 OBJ、给 Rhino/GH 的 CSV。
- `data/`：建筑数据（离线大巴窑；换地方时自动抓的也存这）。

## power_scenarios.yaml 里的三个值
- mult：高度权重。大于 1 长高，小于 1 压低。
- cap_m：高度上限（米）。
- _mode：
  - conserve：总建筑量不变，只在角色之间重新分配。
  - grow：以现有高度为底线往上加，总量上升。

## 固定不变
- 建筑占地
- 角色标签
- 方向单向：由权力推导形态

## 四个角色（+ unknown）
- state：政府公共
- developer：开发商资本
- resident：居民
- informal：在地非正式
- unknown：用途不明，不猜测

## 代码在哪（不用动）
- `engine/common.py`：算（载数据 / 贴角色 / 算高度 / 挤 OBJ）。
- `engine/plots/`：画（每步一个图函数）。
- `engine/steps/`：终端脚本 step0–step5（可选）。

## 边界
- 高度多为估算，少数为实测。
- unknown 不做猜测。
- 教学练习，不是产权认定或规划预测。
