/**
 * workflow_latent_research.mjs
 * =============================================================================
 * 「潜空间生成研究」多智能体工作流(Latent Morphology Studio)
 *
 * 目标:在 05_Shanghai Power to Form 上,把「城市 × 权力体制」的 9 维形态特征
 *      (measure.diagnose)当语料,用**研究方法**自主完成 PCA / AE / VAE 三种编码器:
 *        假设 → 计划 → 写程式 → 验证程式 → 训练 → 审查训练与分析结果 → 迭代修改 → 直到达标
 *      每一步都产出**真实图说**(matplotlib 图 + 中文 caption),最终整理成:
 *        ① 现有专案风格的 engine 后端(latent.py + plots/ + prints/)
 *        ② 使用者教学 ipynb(整合进 05_完整流程「阶段 G」+ 一本独立教学 notebook)
 *        ③ 教学简报(用真实图说)+ 研究报告(双语)
 *
 * 执行方式(本档只写不跑;要跑时):
 *      Workflow({ scriptPath: "05_Shanghai Power to Form Students/latent_research/workflow_latent_research.mjs",
 *                 args: { scale: "full" } })
 *   - args.scale: "min"(~50 agents)/ "std"(~85)/ "full"(~120)。预设 std。
 *   - 全程自动:研究、训练、迭代、打包、简报,无需人工介入(失败的 agent 会降级、不阻断)。
 *
 * 约定(与专案分层契约一致):common/latent 只**算**、plots 只**画**、prints 只**印**、notebook 只**串**。
 * 诚实边界:形态特征为教学抽象、样本小(72),AE/VAE 仅作演示,非统计推断或真实城市预测。
 * =============================================================================
 */

export const meta = {
  name: 'latent-morphology-studio',
  description: '潜空间生成研究:PCA/AE/VAE 训练形态查找表并生成新城市,产出 engine+ipynb+简报(含真实图说)',
  whenToUse: '要在 05 上完整做完 PCA/AE/VAE 的研究、训练、验证、打包与教学简报时',
  phases: [
    { title: 'P0 语料审计', detail: '确认 12 城×6 体制=72 样本的特征资料集可用、画资料概览图' },
    { title: 'P1 研究假设', detail: '多角度提出可证伪假设 + 成功判准(metrics 门槛)' },
    { title: 'P2 设计定案', detail: '4 提案 → 3 评审 → 1 综合:统一 API / 模组佈局 / config schema' },
    { title: 'P3 实作程式', detail: 'worktree 隔离并行写 engine 模组 → 整合者合併' },
    { title: 'P4 验证程式', detail: '单元测试 / 端到端 / torch 缺失路径 / 分层契约 / 可重现' },
    { title: 'P5 训练与超参研究', detail: 'PCA/AE/VAE 三轨 sweep,每个训练真实模型、存指标+图,并对抗验证' },
    { title: 'P6 审查与分析', detail: '重建/生成/潜空间结构/查找表/解耦/稳健/诚实 八维分析(真实图说)' },
    { title: 'P7 迭代修改', detail: '未达判准则精修超参/架构再训练,loop-until-goal(最多数轮)' },
    { title: 'P8 打包交付', detail: '定稿 engine + 整合 notebook 阶段 G + 独立教学 ipynb + 双语指南/报告' },
    { title: 'P9 教学简报', detail: '用真实图说做投影片(Marp md + HTML),逐页配图与讲稿' },
    { title: 'P10 完整性验收', detail: 'completeness critic + 全绿端到端复跑 + 执行摘要' },
  ],
};

// ============================================================================ 常量 / 路径
const ROOT = '05_Shanghai Power to Form Students';
const ENGINE = `${ROOT}/engine`;
const RES = `${ROOT}/latent_research`;          // 研究工作区(报告/图/简报/工作流)
const FIGS = `${RES}/figs`;                      // 真实图说输出根目录(每阶段一子夹)
const DATA_CSV = `${ROOT}/out/latent_research/features.csv`;  // P0 已备妥的语料(12×6=72)
const FEATURES = ['far', 'coverage', 'h_mean', 'h_max', 'h_cv', 'grain', 'slender', 'concentration', 'n'];

// 规模旋钮:依 args.scale 或 token budget 缩放 sweep 数(min≈50 / std≈85 / full≈120 agents)。
const SCALE = (args && args.scale) || 'std';
const K = SCALE === 'full' ? 1.0 : SCALE === 'min' ? 0.45 : 0.72;
const take = (arr) => arr.slice(0, Math.max(1, Math.round(arr.length * K)));   // 依规模截取 sweep 清单

// 每个「训练/分析」agent 都必须遵守的共同守则(注入到 prompt),确保产出真实图说 + 结构化结果。
const RULES = `
【环境】仓库根目录已装好 numpy/pandas/matplotlib/torch/scikit-learn/geopandas；CJK 字型 WenQuanYi Zen Hei 已就绪。
   跑图前务必:import matplotlib; matplotlib.use("Agg"); 并 sys.path.insert(0, "${ENGINE}") 后 import common;common._set_cjk_font()(中文才不会变豆腐)。
【资料】训练语料在 ${DATA_CSV}(欄:slug,name,family,regime + 9 特征 ${FEATURES.join('/')});共 72 列(12 城×6 体制)。
   标准化:对 n、grain 先 log1p 再 z-score(右偏);标准化只 fit 训练集(防洩漏)。
【图说】每个步骤都要产出**真实 matplotlib 图**(PNG,dpi≥120)存到指定 figs 子夹,并写一段中文 caption(≤80字,点出「这张图在说什么」)。
【诚实】样本小、AE/VAE 仅教学演示;别过度宣称。回报里如实写下限制与不确定。
【回传】严格照 schema 回结构化结果(含 figure 路径清单与 caption);别输出多馀散文。`;

// ---------------------------------------------------------------- schema(结构化输出)
const S_HYP = { type: 'object', additionalProperties: false, required: ['hypotheses', 'metrics', 'thresholds'],
  properties: {
    hypotheses: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['id', 'claim', 'test'],
      properties: { id: { type: 'string' }, claim: { type: 'string' }, test: { type: 'string' } } } },
    metrics: { type: 'array', items: { type: 'string' } },
    thresholds: { type: 'array', items: { type: 'string' } } } };

const S_DESIGN = { type: 'object', additionalProperties: false, required: ['api', 'modules', 'config_schema', 'rationale'],
  properties: { api: { type: 'string' }, modules: { type: 'array', items: { type: 'string' } },
    config_schema: { type: 'string' }, rationale: { type: 'string' } } };

const S_JUDGE = { type: 'object', additionalProperties: false, required: ['scores', 'winner', 'grafts'],
  properties: { scores: { type: 'string' }, winner: { type: 'string' }, grafts: { type: 'array', items: { type: 'string' } } } };

const S_CODE = { type: 'object', additionalProperties: false, required: ['files', 'summary', 'selfcheck'],
  properties: { files: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' },
    selfcheck: { type: 'string' } } };

const S_TEST = { type: 'object', additionalProperties: false, required: ['passed', 'failures', 'evidence'],
  properties: { passed: { type: 'boolean' }, failures: { type: 'array', items: { type: 'string' } },
    evidence: { type: 'string' } } };

const S_TRAIN = { type: 'object', additionalProperties: false,
  required: ['model', 'config', 'recon_mse', 'gen_quality', 'figures', 'caption', 'notes'],
  properties: {
    model: { type: 'string' }, config: { type: 'string' },
    recon_mse: { type: 'number' }, gen_quality: { type: 'number' },
    figures: { type: 'array', items: { type: 'string' } },
    caption: { type: 'string' }, notes: { type: 'string' } } };

const S_VERDICT = { type: 'object', additionalProperties: false, required: ['trustworthy', 'reason'],
  properties: { trustworthy: { type: 'boolean' }, reason: { type: 'string' } } };

const S_ANALYSIS = { type: 'object', additionalProperties: false,
  required: ['dimension', 'finding', 'figures', 'caption', 'limitation'],
  properties: { dimension: { type: 'string' }, finding: { type: 'string' },
    figures: { type: 'array', items: { type: 'string' } }, caption: { type: 'string' },
    limitation: { type: 'string' } } };

const S_PACK = { type: 'object', additionalProperties: false, required: ['artifact', 'path', 'summary'],
  properties: { artifact: { type: 'string' }, path: { type: 'string' }, summary: { type: 'string' } } };

const S_SLIDE = { type: 'object', additionalProperties: false, required: ['slide_no', 'title', 'figure', 'script', 'md'],
  properties: { slide_no: { type: 'number' }, title: { type: 'string' }, figure: { type: 'string' },
    script: { type: 'string' }, md: { type: 'string' } } };

// ============================================================================ P0 · 语料审计
phase('P0 语料审计');
const audit = await agent(`${RULES}
你是**资料审计员**。确认 ${DATA_CSV} 存在且为 72 列(12 城×6 体制)。
产出 figs 到 ${FIGS}/P0/:
  1) 特征分布小提琴/箱形图(9 维,标准化后)—— 看尺度与右偏;
  2) 特征相关矩阵热图 —— 看共线性;
  3) 依 family 的样本数长条 —— 看类别不平衡。
回报资料品质(缺值/离群/共线性)与对后续建模的启示。`,
  { phase: 'P0 语料审计', schema: S_ANALYSIS });
log(`P0 完成:${audit ? audit.finding?.slice(0, 60) : '（降级)'}`);

// ============================================================================ P1 · 研究假设(多角度 fan-out)
phase('P1 研究假设');
const hypAngles = [
  '重建忠实度:AE 在小样本下重建 MSE 应低于 PCA;VAE 因 KL 会略高但潜空间更适合采样。',
  '生成合理性:VAE 从 N(0,I) 采样的新城市,9 特征应落在训练包络内、无不可能值(如负高度)。',
  '潜空间结构:同一形态家族/权力体制在潜空间应可分(silhouette > 0)。',
  '查找表检索:leave-one-city-out 下,潜空间最近邻应能召回同家族。',
  '维度权衡:latent_dim 从 2→3→4,重建↑但可视化/教学价值↓,需找教学甜蜜点。',
  '权力轴向:PCA 主成分/VAE latent traversal 是否对应可解读的形态轴(塔化、集权、细粒)。',
];
const hypotheses = (await parallel(take(hypAngles).map((a, i) => () =>
  agent(`${RULES}\n你是**研究提问者 H${i + 1}**。围绕此角度提出 1-2 个**可证伪**假设、要量测的 metrics、以及达标门槛(具体数值)。角度:${a}`,
    { phase: 'P1 研究假设', schema: S_HYP, label: `hyp:${i + 1}` }))
)).filter(Boolean);
log(`P1 完成:收集 ${hypotheses.length} 组假设`);

// ============================================================================ P2 · 设计定案(judge panel)
phase('P2 设计定案');
const proposals = [
  'numpy-first:PCA 纯 numpy SVD,AE/VAE 用 torch 且「缺 torch 友好跳过」;最小依赖、最贴教学。',
  'sklearn-unified:PCA/标准化用 sklearn,AE/VAE 用 torch;借力成熟库、少写数值码。',
  'torch-unified:三者都用 torch,统一训练回圈与介面;一致但 PCA 也需 torch。',
  'research-grade:config 驱动 + 严谨 train/val/test + 实验登记;最利研究、稍重。',
];
const props = (await parallel(proposals.map((p, i) => () =>
  agent(`${RULES}\n你是**架构提案者 D${i + 1}**。就此路线给出:统一 API(fit/encode/decode/generate)、模组佈局(latent.py + plots/latent_space.py + prints/latent.py)、config schema、取捨理由。路线:${p}`,
    { phase: 'P2 设计定案', schema: S_DESIGN, label: `design:${i + 1}` }))
)).filter(Boolean);
const judges = (await parallel(['正确性', '教学契合', '可维护性'].map((lens, i) => () =>
  agent(`${RULES}\n你是**评审 J${i + 1}(${lens} lens)**。依此面向评比以下提案并选优、指出各提案值得移植的亮点。\n提案:\n${JSON.stringify(props)}`,
    { phase: 'P2 设计定案', schema: S_JUDGE, label: `judge:${lens}` }))
)).filter(Boolean);
const design = await agent(`${RULES}\n你是**综合架构师**。综合以下评审结论,产出**最终设计定案**(单一 API、模组佈局、config schema、命名对齐最新 master 的 feature 用语)。\n提案:${JSON.stringify(props)}\n评审:${JSON.stringify(judges)}`,
  { phase: 'P2 设计定案', schema: S_DESIGN, label: 'design:final', effort: 'high' });
log(`P2 定案:${design ? design.modules?.join(', ') : '（降级)'}`);

// ============================================================================ P3 · 实作程式(worktree 隔离并行 → 整合)
phase('P3 实作程式');
const modSpecs = [
  ['latent.py::Standardizer+PCAEncoder', '写 engine/latent.py 的 Standardizer(log+z-score 可逆)与 PCAEncoder(numpy SVD;fit/encode/decode/generate/recon;evr_)。'],
  ['latent.py::AEEncoder', '写 AEEncoder(torch;encoder d→h→k、decoder 对称;MSE 训练;缺 torch 抛清楚错误让上层跳过)。'],
  ['latent.py::VAEEncoder', '写 VAEEncoder(torch;重参数化;recon+beta*KL;encode 取 mu;generate 从 N(0,I) 采样)。'],
  ['latent.py::LatentStudy+fit_all', '写 LatentStudy 门面(codes/table/recon_error/generate/nearest/interpolate)与 fit_all 一行入口。'],
  ['latent.py::feature_table', '写 feature_table(城市×体制→9 特征;对齐 feature 命名;存 out/latent_research/features.csv)。'],
  ['plots/latent_space.py', '写 latent_scatter(查找表地图+生成★+插值虚线)、reconstruction、recon_error_bars;autosave 契约。'],
  ['prints/latent.py', '写 latent_ready/recon_errors/lookup_table/generated/nearest(只印人话)。'],
  ['__init__ 登记', '在 plots/__init__.py、prints/__init__.py 登记新函式;engine/requirements.txt 补 torch(可选)。'],
];
const built = await pipeline(
  modSpecs,
  ([name, task], _orig, i) => agent(`${RULES}\n你是**实作者 I${i + 1}**,负责「${name}」。依设计定案实作,风格对齐现有 engine(中文 docstring、分层契约)。设计:${JSON.stringify(design)}\n任务:${task}\n完成后做 py_compile 自检并回报。`,
    { phase: 'P3 实作程式', schema: S_CODE, label: `impl:${name}`, isolation: 'worktree' }),
);
const integrator = await agent(`${RULES}\n你是**整合者**。把各 worktree 的模组合併到主工作树,解决冲突,确保 import 一致、py_compile 全过、与既有 notebook 契约相容。回报最终档案清单与自检。\n各模组:${JSON.stringify(built.filter(Boolean))}`,
  { phase: 'P3 实作程式', schema: S_CODE, label: 'impl:integrate', effort: 'high' });
log(`P3 完成:整合 ${integrator ? integrator.files?.length : 0} 档`);

// ============================================================================ P4 · 验证程式
phase('P4 验证程式');
const testSpecs = [
  '单元测试:Standardizer 可逆(transform→inverse 还原)、PCA encode/decode 形状与重建、generate 形状。',
  '单元测试:AE/VAE encode/decode/generate/nearest/interpolate 数学正确(有 torch 时)。',
  'torch 缺失路径:模拟无 torch,确认 PCA 照跑、AE/VAE 友好跳过不 crash。',
  '端到端:sys.path 指 engine,fit_all 跑真实 3 站与 12 站,产出 study/codes/generate 无误。',
  '分层契约:latent 只算不画、plots 只画、prints 只印;检查无越界 import。',
  '可重现:固定 seed 两次训练结果一致(容差内)。',
];
const tests = (await parallel(take(testSpecs).map((t, i) => () =>
  agent(`${RULES}\n你是**验证者 Q${i + 1}**。撰写并**实际执行**此测试,附证据(指令与输出摘要)。发现 bug 就明确指出可修点。\n测试:${t}`,
    { phase: 'P4 验证程式', schema: S_TEST, label: `test:${i + 1}` }))
)).filter(Boolean);
const testFails = tests.filter(t => t && t.passed === false);
if (testFails.length) {
  log(`P4 发现 ${testFails.length} 项失败 → 触发修补`);
  await agent(`${RULES}\n你是**修补者**。依失败项修正 engine 程式并复跑测试至通过。失败:${JSON.stringify(testFails)}`,
    { phase: 'P4 验证程式', schema: S_TEST, label: 'test:fix', effort: 'high' });
}

// ============================================================================ P5 · 训练与超参研究(三轨 sweep + 对抗验证)
phase('P5 训练与超参研究');
const pcaSweeps = [
  'PCA k=2', 'PCA k=3', 'PCA k=4', 'PCA whitening=on', 'PCA 无 log 变体(对照)',
].map(s => ({ model: 'PCA', cfg: s }));                                        // 5
const aeSweeps = [
  'AE latent=2 hidden=16', 'AE latent=3 hidden=32', 'AE latent=4 hidden=32',
  'AE denoising(加噪)', 'AE Huber loss + weight_decay', 'AE ReLU+BN',
  'AE lr=5e-3 epochs=1200', 'AE 多 seed(0/1/2)稳定性',
].map(s => ({ model: 'AE', cfg: s }));                                         // 8
const vaeSweeps = [
  'VAE latent=2 beta=0.1', 'VAE latent=2 beta=0.5', 'VAE latent=2 beta=1.0', 'VAE latent=2 beta=4.0(beta-VAE)',
  'VAE latent=3 beta=0.5', 'VAE KL annealing', 'VAE posterior-collapse 侦测',
  'VAE decoder σ 学习', 'VAE 多 seed 稳定性', 'VAE latent traversal',
].map(s => ({ model: 'VAE', cfg: s }));                                        // 10
const baselines = [
  'baseline: 每家族均值±std 生成', 'baseline: KMeans 群心当 codebook',
].map(s => ({ model: 'BASE', cfg: s }));                                       // 2  → 合计 25 trainer(×verify=50)
const allSweeps = [...take(pcaSweeps), ...take(aeSweeps), ...take(vaeSweeps), ...take(baselines)];
log(`P5 sweep 数:${allSweeps.length}(每个训练→对抗验证)`);

// pipeline:每个 sweep「训练→存图→对抗验证」独立流水,不设 barrier。
const trainResults = await pipeline(
  allSweeps,
  (spec, _o, i) => agent(`${RULES}\n你是**训练研究员 T${i + 1}**(${spec.model})。用 ${DATA_CSV},以 city-grouped 切分做训练/验证,配置:「${spec.cfg}」。
  实际训练模型,量测 recon_mse、生成品质(gen_quality: 生成样本落在训练包络的比例 × 与最近真实样本的相似度,0~1),
  并产出 figs 到 ${FIGS}/P5/:训练曲线(若适用)、潜空间散点、重建对比。回报结构化结果 + 图路径 + 中文 caption。`,
    { phase: 'P5 训练与超参研究', schema: S_TRAIN, label: `train:${spec.model}:${i + 1}`, effort: 'low' }),
  (res, spec) => res ? agent(`${RULES}\n你是**对抗验证员**。严格检查此训练结果是否可信(过拟合?posterior collapse?生成含不可能值?图与数字是否自洽?),预设倾向不可信除非证据充分。\n结果:${JSON.stringify(res)}`,
    { phase: 'P5 训练与超参研究', schema: S_VERDICT, label: `verify:${spec.model}` }).then(v => ({ ...res, verdict: v })) : null,
);
const trusted = trainResults.filter(Boolean).filter(r => r.verdict && r.verdict.trustworthy);
log(`P5 完成:${trainResults.filter(Boolean).length} 训练,${trusted.length} 通过对抗验证`);

// 选模:从可信结果挑各 model 最佳配置(recon 与 gen 综合)。
const selection = await agent(`${RULES}\n你是**选模综合师**。从通过验证的结果中,为 PCA/AE/VAE 各选一组**预设配置**(平衡重建、生成、教学可视化),并产出一张三模型比较总图(recon vs gen)到 ${FIGS}/P5/。给出选定 latent_dim/beta/epochs 等。\n可信结果:${JSON.stringify(trusted)}`,
  { phase: 'P5 训练与超参研究', schema: S_ANALYSIS, label: 'select:defaults', effort: 'high' });

// ============================================================================ P6 · 审查与分析(八维,真实图说)
phase('P6 审查与分析');
const dims = [
  ['重建忠实度', '逐特征 R²/MSE,PCA vs AE vs VAE,指出各自失真在哪。'],
  ['生成合理性', '生成新城市的 9 特征分布 vs 训练包络;标出越界/不可能值。'],
  ['潜空间结构', '依 family/regime 上色的潜空间散点 + silhouette 分数。'],
  ['查找表检索', 'leave-one-city-out 最近邻召回同家族的准确率曲线。'],
  ['维度权衡', 'latent_dim 2/3/4 的重建-可解释权衡曲线。'],
  ['权力轴向解读', 'PCA loadings 与 VAE latent traversal 对应的形态语义。'],
  ['稳健性', '多 seed 的结果变异;新城市 OOD 行为。'],
  ['诚实边界', '小样本过拟合证据、别过度宣称的清单(教学告示)。'],
];
const analyses = (await parallel(dims.map(([d, task], i) => () =>
  agent(`${RULES}\n你是**分析师 A${i + 1}(${d})**。基于选定模型与 P5 结果,产出此维度的**真实图说**到 ${FIGS}/P6/ 并给出发现与限制。任务:${task}\n选定:${JSON.stringify(selection)}`,
    { phase: 'P6 审查与分析', schema: S_ANALYSIS, label: `analyze:${d}` }))
)).filter(Boolean);
log(`P6 完成:${analyses.length} 维分析`);

// ============================================================================ P7 · 迭代修改(loop-until-goal)
phase('P7 迭代修改');
let round = 0;
let goalMet = false;
while (!goalMet && round < 2) {                       // 最多 2 轮迭代(护住 agent 总量上限)
  round += 1;
  const gate = await agent(`${RULES}\n你是**达标裁决**。对照 P1 的假设与门槛,判断当前结果是否达标;未达标就明确指出**待改点**(哪个模型/超参/图)。\n假设:${JSON.stringify(hypotheses)}\n分析:${JSON.stringify(analyses)}\n选定:${JSON.stringify(selection)}`,
    { phase: 'P7 迭代修改', schema: S_VERDICT, label: `gate:r${round}`, effort: 'high' });
  if (gate && gate.trustworthy) { goalMet = true; log(`P7 第 ${round} 轮:达标`); break; }
  log(`P7 第 ${round} 轮:未达标 → 精修再训练`);
  const refine = ['精修最弱模型超参并重训', '改善生成越界(裁剪/温度/prior)', '补一张更清楚的图说'];
  await parallel(refine.map((t, i) => () =>
    agent(`${RULES}\n你是**精修者 R${round}.${i + 1}**。依待改点执行并复跑,产出更新后的图/指标。待改:${gate ? gate.reason : ''}\n任务:${t}`,
      { phase: 'P7 迭代修改', schema: S_TRAIN, label: `refine:r${round}:${i + 1}` }))
  );
}

// ============================================================================ P8 · 打包交付(engine + notebook + 双语文件)
phase('P8 打包交付');
const packJobs = [
  ['engine 定稿', `把选定预设写回 engine/latent.py 的 fit_all/LatentStudy 预设;确保 plots/prints 契约完整;py_compile 全过。选定:${JSON.stringify(selection)}`],
  ['整合 notebook 阶段 G', `在 ${ROOT}/05_完整流程.ipynb 新增/更新「阶段 G · 潜空间」:setup 补 import latent + 热重载;一行入口 fit_all → 编码(查找表)→ 生成新城市 → 最近邻;每格附中文说明。自成一段、不依赖前面中间变数。`],
  ['独立教学 ipynb', `建 ${RES}/生成册_教学.ipynb:一本从零到一的教学 notebook(资料→标准化→PCA/AE/VAE→查找表→生成→插值),每步嵌入 P5/P6 的真实图说与讲解,面向学生。`],
  ['双语指南', `写 ${RES}/生成册指南_简体.md 与 _繁體.md:如何用、如何换城市、如何改超参、如何加自己的编码器(对齐算子替换指南风格)。`],
  ['研究报告', `写 ${RES}/研究报告.md(简+繁摘要):假设→方法→实验→结果(嵌真实图)→选定预设→诚实边界。`],
];
const packed = await pipeline(
  packJobs,
  ([name, task], _o, i) => agent(`${RULES}\n你是**打包者 K${i + 1}**,交付「${name}」,风格对齐现有专案。任务:${task}`,
    { phase: 'P8 打包交付', schema: S_PACK, label: `pack:${name}` }),
);
log(`P8 完成:${packed.filter(Boolean).length} 项交付`);

// ============================================================================ P9 · 教学简报(真实图说)
phase('P9 教学简报');
const slideOutline = await agent(`${RULES}\n你是**简报总监**。规划一份 10-12 页教学简报大纲(动机→资料→三模型→查找表→生成新城市→迭代→限制→结论),每页指定要用哪张**真实图**(从 ${FIGS}/ 挑)。回报大纲。`,
  { phase: 'P9 教学简报', schema: S_ANALYSIS, label: 'slides:outline', effort: 'high' });
const slideNos = take([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
const slides = (await parallel(slideNos.map((n) => () =>
  agent(`${RULES}\n你是**简报页作者 P${n}**。产出第 ${n} 页:标题、选用的真实图路径、讲稿(口语、≤120字)、Marp markdown 片段。大纲:${JSON.stringify(slideOutline)}`,
    { phase: 'P9 教学简报', schema: S_SLIDE, label: `slide:${n}` }))
)).filter(Boolean);
await agent(`${RULES}\n你是**简报组装者**。把各页组成 ${RES}/slides/生成册简报.md(Marp)并转出 ${RES}/slides/生成册简报.html(内嵌真实图);确保每页有图有讲稿。\n各页:${JSON.stringify(slides)}`,
  { phase: 'P9 教学简报', schema: S_PACK, label: 'slides:assemble', effort: 'high' });

// ============================================================================ P10 · 完整性验收
phase('P10 完整性验收');
const critic = await agent(`${RULES}\n你是**完整性评论者**。检查:engine 是否可 import 且契约完整、notebook 阶段 G 是否可 Run All、独立教学 ipynb 是否自洽、指南/报告/简报是否都用了真实图、有无未验证宣称或缺漏图说。列出缺口。`,
  { phase: 'P10 完整性验收', schema: S_ANALYSIS, label: 'critic:completeness', effort: 'high' });
const finalVerify = (await parallel([
  '端到端复跑:notebook 阶段 G 用 nbconvert 执行到底、无错。',
  'engine 复跑:python 端 fit_all 全流程 + 三模型生成 + 最近邻,截取输出为证。',
].map((t, i) => () =>
  agent(`${RULES}\n你是**最终验收员 F${i + 1}**。实际执行并回报是否全绿。任务:${t}\n缺口参考:${critic ? critic.finding : ''}`,
    { phase: 'P10 完整性验收', schema: S_TEST, label: `final:${i + 1}`, effort: 'high' }))
)).filter(Boolean);
const summary = await agent(`${RULES}\n你是**执行摘要综合师**。用双语写一段总结:做了什么、达成哪些假设、选定预设、交付清单(engine/notebook/指南/报告/简报路径)、诚实边界与后续建议。存到 ${RES}/研究报告.md 的开头。\n验收:${JSON.stringify(finalVerify)}\n缺口:${JSON.stringify(critic)}`,
  { phase: 'P10 完整性验收', schema: S_PACK, label: 'final:summary', effort: 'high' });

log('工作流完成:engine + ipynb + 指南 + 报告 + 简报(含真实图说)已产出。');
return {
  scale: SCALE,
  data_rows: 72,
  design: design && design.modules,
  trained: trainResults.filter(Boolean).length,
  trusted: trusted.length,
  selection: selection && selection.finding,
  analyses: analyses.length,
  iterated_rounds: round,
  packaged: packed.filter(Boolean).map(p => p && p.path),
  slides: slides.length,
  final_green: finalVerify.every(f => f && f.passed),
  summary: summary && summary.summary,
};
