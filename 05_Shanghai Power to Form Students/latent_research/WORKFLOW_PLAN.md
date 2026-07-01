# 潜空间生成研究 · 工作流详细档(Latent Morphology Studio)

> 本档说明 `workflow_latent_research.mjs` 的**研究方法、分工、图说规格、产出与跑法**。
> 现阶段:**只写不跑**。核准后再执行。

---

## 0. 一句话

把「城市 × 权力体制」的 **9 维形态特征**(`measure.diagnose`)当语料,用**研究方法**
(假设 → 计划 → 写程式 → 验证 → 训练 → 审查分析 → 迭代 → 达标)自主训练 **PCA / AE / VAE**,
每步都出**真实图说**,最终整理成**现有专案风格的 engine 后端 + 教学 ipynb + 教学简报**。

- 语料已备妥:`out/latent_research/features.csv` —— **12 城 × 6 体制 = 72 样本 × 9 特征**(已实跑产生)。
- 特征:`far / coverage / h_mean / h_max / h_cv / grain / slender / concentration / n`。
- 命名对齐最新 master(重构后用 **feature** 而非 fingerprint)。

---

## 1. 研究流程(对应你要的「像研究一样」)

```
P0 语料审计 ─▶ P1 假设 ─▶ P2 设计 ─▶ P3 写程式 ─▶ P4 验证程式
        └────────────────────────────────────────────────┘
                          ▼
        P5 训练+超参研究 ─▶ P6 审查与分析 ─▶ P7 迭代修改(未达标就回去再训)
                          │                        │
                          └──── loop until goal ───┘
                                     ▼
        P8 打包(engine + ipynb) ─▶ P9 教学简报 ─▶ P10 完整性验收
```

每个阶段都要求 agent 产出**真实 matplotlib 图(PNG)+ 中文 caption(图说)**,存到 `latent_research/figs/<阶段>/`。

---

## 2. 阶段分工(详细)

| 阶段 | 角色 | 做什么 | 真实图说产出 |
|---|---|---|---|
| **P0 语料审计** | 资料审计员 ×1 | 确认 72 样本;查缺值/离群/共线性 | 特征分布图、相关矩阵热图、家族样本数长条 |
| **P1 研究假设** | 研究提问者 ×N | 6 角度提**可证伪**假设 + metrics + 达标门槛 | (文字为主) |
| **P2 设计定案** | 提案者 ×4 → 评审 ×3 → 综合 ×1 | 4 路线(numpy-first / sklearn / torch / research-grade)→ 3 lens 评审 → 定案 API/模组/config | 架构示意 |
| **P3 实作程式** | 实作者 ×8(**worktree 隔离**)+ 整合者 ×1 | 并行写 `latent.py`/`plots`/`prints`,再合併、`py_compile` | — |
| **P4 验证程式** | 验证者 ×N + 修补者(条件) | 单元/端到端/torch 缺失路径/分层契约/可重现;失败即修 | — |
| **P5 训练+超参研究** | 训练研究员 ×25 + 对抗验证员 ×25 + 选模师 ×1 | 三轨 sweep 各自**真实训练**、量 recon/gen、每个都被对抗验证;选定预设 | 训练曲线、潜空间散点、重建对比、三模型比较总图 |
| **P6 审查与分析** | 分析师 ×8 | 八维分析(见下)各出图说 | 逐特征 R²、生成包络、silhouette、检索召回、维度权衡、loadings/traversal、多 seed 变异、诚实清单 |
| **P7 迭代修改** | 达标裁决 ×1 + 精修者 ×3 /轮(≤2 轮) | 对照 P1 门槛;未达标就精修超参/架构再训 | 更新后的图/指标 |
| **P8 打包交付** | 打包者 ×5 | engine 定稿、notebook 阶段 G、独立教学 ipynb、双语指南、研究报告 | 报告内嵌真实图 |
| **P9 教学简报** | 总监 ×1 + 页作者 ×10 + 组装 ×1 | 10 页教学投影片(Marp md + HTML),逐页配**真实图** + 讲稿 | 每页一张真实图 |
| **P10 完整性验收** | 评论者 ×1 + 验收员 ×2 + 摘要 ×1 | 缺口检查 + 端到端全绿复跑 + 双语执行摘要 | — |

### P5 三轨 sweep(核心)
- **PCA 轨(5)**:k=2/3/4、whitening、无 log 对照 —— scree 与主轴可解释性。
- **AE 轨(8)**:latent 2/3/4、denoising、Huber+weight_decay、ReLU+BN、lr/epochs、多 seed。
- **VAE 轨(10)**:β=0.1/0.5/1/4(β-VAE)、latent=3、KL annealing、posterior-collapse、decoder σ、多 seed、latent traversal。
- **对照(2)**:家族均值±std 生成、KMeans 群心当 codebook。
- 每个 sweep 走 `pipeline`「训练 → 对抗验证」独立流水(无 barrier),只有**通过验证**的结果进入选模。

### P6 八维分析
重建忠实度 · 生成合理性 · 潜空间结构 · 查找表检索 · 维度权衡 · 权力轴向解读 · 稳健性 · 诚实边界。

---

## 3. 真实图说规格(每张图的约定)

- 后端 `matplotlib.use("Agg")`;`sys.path.insert(0,"engine")` 后 `import common; common._set_cjk_font()`
  → 中文用已就绪的 **WenQuanYi Zen Hei**,不会变豆腐方块。
- PNG,`dpi≥120`,存 `latent_research/figs/<阶段>/NN_名称.png`。
- 每张图附**中文 caption(≤80 字)**:点出「这张图在说什么、看哪里」。
- 供 P9 简报直接引用(简报 = 真实图 + 讲稿,不另造示意图)。

---

## 4. 交付物(P8/P9 完成后)

| 类型 | 路径 | 说明 |
|---|---|---|
| engine | `engine/latent.py` | Standardizer + PCA/AE/VAE + LatentStudy + fit_all + feature_table |
| engine | `engine/plots/latent_space.py` | latent_scatter / reconstruction / recon_error_bars |
| engine | `engine/prints/latent.py` | latent_ready / recon_errors / lookup_table / generated / nearest |
| notebook | `05_完整流程.ipynb` 阶段 G | 整合进主流程(setup 补 import + 一行入口) |
| notebook | `latent_research/生成册_教学.ipynb` | 从零到一的独立教学本(嵌真实图) |
| 文件 | `latent_research/生成册指南_简体.md` / `_繁體.md` | 使用与扩充指南 |
| 报告 | `latent_research/研究报告.md` | 假设→方法→实验→结果(真实图)→选定预设→诚实边界 |
| 简报 | `latent_research/slides/生成册简报.md` + `.html` | 教学投影片(真实图 + 讲稿) |
| 图 | `latent_research/figs/**` | 各阶段真实图说 |

---

## 5. Agent 规模(依 `args.scale` 缩放)

`take()` 依规模系数 K 截取各 sweep 清单(固定成本阶段不缩)。实际总量(典型值):

| scale | K | 约略 agent 数 | 用途 |
|---|---|---|---|
| `min` | 0.45 | **≈ 75** | 快速走一遍全流程 |
| `std`(预设) | 0.72 | **≈ 95** | 平衡覆盖与成本 |
| `full` | 1.0 | **≈ 115**(worst ≤ 120) | 最完整的超参研究与分析 |

> 主要成本在 P5(25 训练 × 各 1 对抗验证 = 50)。P7 迭代封顶 2 轮以护住上限。
> runtime 自动限制并发(约 10–16),总量硬上限 1000;本工作流设计恒 ≤ 120。

---

## 6. 护栏

- **worktree 隔离**:仅 P3(并行改档)用 `isolation:'worktree'`,避免写档冲突;其馀唯读/研究不用(省成本)。
- **对抗验证**:P5 每个训练结果、P4 每项修补都由独立 skeptic 检查(过拟合 / posterior collapse / 生成越界 / 图数不符)。
- **loop-until-goal**:P7 对照 P1 门槛,未达标才再训;达标即停。
- **no silent caps**:若因规模截断 sweep,`log()` 会说明截掉了什么。
- **诚实边界**:样本小(72)、AE/VAE 仅教学演示,报告与 notebook 明载限制,不过度宣称。

---

## 7. 跑法(核准后)

```js
Workflow({
  scriptPath: "05_Shanghai Power to Form Students/latent_research/workflow_latent_research.mjs",
  args: { scale: "full" }        // "min" / "std" / "full"
})
```

- 背景执行,完成后回报 `{trained, trusted, selection, packaged, slides, final_green, summary}`。
- 可用 `/workflows` 看即时进度;中途要停用 `TaskStop`,改脚本后可 `resumeFromRunId` 续跑(未变的 agent 走快取)。

---

## 8. 目前状态

- [x] 语料已实跑产生(`out/latent_research/features.csv`,72×9)
- [x] 工作流脚本已写、JS 语法已验证(`workflow_latent_research.mjs`)
- [x] 本详细档
- [ ] **执行**(等你核准;预设 `scale:"std"`)
