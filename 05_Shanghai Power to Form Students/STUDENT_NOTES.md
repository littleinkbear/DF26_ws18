# 速查

## 一句话
上海真实多源数据 → 贴角色 →（主册）只调高度 /（进阶）算子配方 → 看天际线 / 形态指纹。

## 5 本 notebook(按顺序)
1. `01_数据-怎么选与拼接` —— 怎么选数据、多源怎么拼、从数据集建缓存。
2. `02_映射-谁算谁的` —— 离散级联查表:一栋=一个权利方。
3. `03_城市天际线-动手做` —— **主册**:只调高度,看天际线。
4. `04_进阶-权力算子` —— **进阶**:9 算子 × 4 体制 → 形态指纹。
5. `05_换地方-按街道取` —— **换地方**:按街道取(随包 9 街道切 / 按街道名现建)。

## 能改的文件(就在这个文件夹,不用进 engine)
- `config.py` —— 换站点 `SLUG`(lujiazui / caoyang / yuyuan);进阶填 `DATASET_ROOT`。
- `shanghai_lookup.yaml` —— 谁算谁的。改完重跑 Step 2。
- `power_scenarios.yaml` —— 高度政策。改完重跑 Step 3、4。
- `regimes.yaml` —— 算子配方(进阶)。
- 加算子:`算子替换指南.md` + `engine/my_operator.py`。

## power_scenarios.yaml 三个值
- `mult`:高度权重。>1 长高,<1 压低。
- `cap_m`:高度上限(米)。
- `_mode`:`conserve` 总量守恒、只重分配 / `grow` 只增不减。

## 9 个原子算子(进阶)
`freeze` 锁定 · `weight_height` 按权重重分配高度 · `concentrate` 向权力重心收拢 ·
`split_to_towers` 拆板成塔 · `slim` 塔化 · `densify` 加密 · `infill` 居民自建细分 ·
`level` 平权趋同 · `open_ground` 释放共享地面。**权力体制 = 这些动词的配方。**

## 四种权力 → 四种形态指纹
- 开发商主导 = 细针塔(瘦长比飙升)
- 政府主导/集权 = 向权力重心收拢的肥峰(重心集中度翻倍)
- 居民自建 = 细粒碎化(栋数大增)
- 共享平权 = 均质开放(高度 CV 最低)

## 五个角色(+ informal 恒空)
- `state` 政府/公共 · `developer` 开发商/资本 · `resident` 居民 ·
- `unknown` 无用途 join · `informal` 本数据无信号 → 恒为空(不硬猜)。

## 固定不变
- 建筑占地 footprint（主册）· 角色标签 · 方向单向:由权力推导形态。

## 产物在哪
- `out/<slug>/`:图 PNG、3D OBJ、CSV、`report.html`(繁体自含单档)。
- `data/<slug>/`:缓存(随包 3 站;自己建的也存这)。

## 边界
- 高度 AI 实测、极超高层可能低估 · EULUC 面级优先 · danwei 看不见(算居民)·
  informal 恒空 · 进阶算子是教学假设 · 教学练习,非产权认定或规划预测。
