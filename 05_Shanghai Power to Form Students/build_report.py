"""
build_report.py — 单站点全套产出:图 + 卫星 + 静态对比 + 浅色互动 3D + 进阶算子,自含单档 report.html(繁体)
=================================================================
给一个 slug(站点),用 engine 的本地多源数据生成:
  out/<slug>/satellite.png · satellite_overlay.png   先看真实的地方(Esri 卫星 + 我们的离散读法)
  out/<slug>/step1_buildings.png                      看楼:实测高度的真实 footprint
  out/<slug>/step2_stakeholders.png                   离散级联查表:一栋=一个 stakeholder
  out/<slug>/step3_policies.png · step4_metrics.png   高度政策热图 / 各情景指标
  out/<slug>/scenarios_3d.png                         静态 3D 对比(同视角,可截图)
  out/<slug>/regimes.png · fingerprints.png           进阶:9 算子 × 4 权力体制 → 形态指纹
  out/<slug>/city_current.obj · city_developer_led.obj + buildings_export.csv   进 Rhino/GH
  out/<slug>/report.html                              自含单档:卫星在前 + 浅色互动 3D + 方法走读 + 进阶算子(繁体)
数字全部由 pipeline 实算注入(改 YAML 重跑即同步)。零 AI。HTML 交付物为繁体(opencc s2t)。
跑:python3 build_report.py            # 三站全套 + out/index.html
   python3 build_report.py caoyang    # 只跑单站
"""
import base64, json, warnings, sys, os
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
import config
import common as C
import operators as ops
import measure as M
import plots
import report
from report import (ACCENT, SH_ORDER, SHOW, _t, _zh_hant, traditionalize_engine_labels,
                    load, compute_stats, color_of, fig_step1, fig_step2, fig_step3, fig_step4,
                    fig_scenarios_3d, fig_satellite, fig_operators, export_obj, build_geometry, _footprint_bounds)

ROOT = C.ROOT
OUT = C.OUT
WEB = ROOT / "web"


def fig_block(slug, name, cap):
    p = OUT / slug / name
    if not p.exists():   # 离线时卫星图可能没生成 → 优雅占位,不让报告崩
        return '<figure><figcaption>（%s — 此图需联网生成,已跳过）</figcaption></figure>' % cap
    b64 = base64.b64encode(p.read_bytes()).decode()
    return '<figure><img src="data:image/png;base64,%s" alt="%s"><figcaption>%s</figcaption></figure>' % (b64, cap, cap)


CSS = """
:root{--accent:#0f5e63;--ink:#1a1f22;--muted:#717b80;--line:#e6e9ea;--bg:#f7f8f7;
 --state:#5b86c4;--developer:#e08763;--resident:#7bbf86;--informal:#dcc04e;--unknown:#9aa3a6;}
*{box-sizing:border-box;} html{scroll-behavior:smooth;}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 "Helvetica Neue","PingFang SC","Microsoft YaHei",system-ui,sans-serif;}
.wrap{max-width:1080px;margin:0 auto;padding:0 22px 90px;}
.cover{max-width:1180px;margin:0 auto;padding:30px 22px 4px;}
.cover .kick{letter-spacing:.18em;text-transform:uppercase;font-size:11px;color:var(--muted);margin:0 0 8px;}
.cover h1{font-size:27px;line-height:1.3;margin:0 0 8px;font-weight:750;}
.cover p.lead{margin:0 0 16px;color:#3a4347;max-width:830px;font-size:15.5px;}
.sat2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
@media(max-width:760px){.sat2{grid-template-columns:1fr;}}
.hero{max-width:1180px;margin:16px auto 0;padding:0 22px;}
.hero p.lead2{margin:0 0 10px;color:var(--muted);font-size:14px;}
#stage{position:relative;width:100%;height:60vh;min-height:420px;border-radius:12px;overflow:hidden;background:#eaeef0;border:1px solid var(--line);}
#cv3d{width:100%;height:100%;display:block;}
.hud{position:absolute;left:14px;top:14px;display:flex;flex-direction:column;gap:9px;max-width:300px;}
.scn{display:flex;flex-wrap:wrap;gap:6px;}
.scn button{font:inherit;font-size:12.5px;font-weight:600;border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:20px;padding:5px 12px;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,.06);}
.scn button.on{background:var(--accent);border-color:var(--accent);color:#fff;}
.hud .card{background:rgba(255,255,255,.92);backdrop-filter:blur(6px);border:1px solid var(--line);border-radius:10px;padding:10px 13px;font-size:12.5px;box-shadow:0 1px 6px rgba(0,0,0,.08);}
.hud .metric{display:flex;justify-content:space-between;gap:14px;padding:1px 0;} .hud .metric b{font-variant-numeric:tabular-nums;}
.legend{display:flex;flex-wrap:wrap;gap:8px 12px;margin-top:4px;font-size:12px;}
.legend i{width:11px;height:11px;border-radius:3px;display:inline-block;margin-right:5px;vertical-align:-1px;}
.toggle{font-size:12px;color:var(--muted);} .toggle a{color:var(--accent);cursor:pointer;text-decoration:underline;}
.hint3d{position:absolute;right:14px;bottom:12px;font-size:11.5px;color:#5a6468;background:rgba(255,255,255,.72);padding:2px 7px;border-radius:6px;}
.herofoot{max-width:1180px;margin:0 auto;padding:10px 22px 6px;font-size:12.5px;color:var(--muted);}
h2{font-size:20px;margin:46px 0 12px;border-bottom:2px solid var(--accent);padding-bottom:7px;}
h2 .num{display:inline-block;background:var(--accent);color:#fff;font-size:12px;font-weight:700;padding:3px 9px;border-radius:4px;margin-right:11px;vertical-align:middle;}
p{margin:0 0 13px;} b{color:#0c4a4e;} code{background:#eaf0f0;color:#0a4448;padding:1px 6px;border-radius:4px;font-size:.88em;font-family:"SF Mono",Menlo,monospace;}
.teach{background:#eaf4f4;border-left:4px solid var(--accent);padding:10px 15px;border-radius:0 6px 6px 0;font-size:14.5px;margin:13px 0 0;}
.teach .tag{display:inline-block;background:var(--accent);color:#fff;font-size:11px;font-weight:700;padding:2px 8px;border-radius:4px;margin-right:9px;}
figure{margin:16px 0 6px;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff;}
figure img{display:block;width:100%;height:auto;} figcaption{font-size:12.5px;color:var(--muted);padding:8px 13px;background:#f3f5f5;border-top:1px solid var(--line);}
table{border-collapse:collapse;width:100%;margin:10px 0 16px;font-size:14px;} th,td{border:1px solid var(--line);padding:8px 11px;text-align:center;} thead th{background:var(--accent);color:#fff;} tbody tr:nth-child(odd){background:#f5f8f8;}
.chips{margin:8px 0;} .chip{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid var(--line);border-radius:20px;padding:4px 11px 4px 8px;margin:0 7px 7px 0;font-size:13px;} .chip .dot{width:11px;height:11px;border-radius:50%;}
.honest{background:#fff;border:1px solid var(--line);border-radius:10px;padding:6px 22px 16px;margin-top:40px;} .honest h2{border-bottom-color:#c0654a;} .honest li{margin:0 0 8px;font-size:14px;}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);text-align:center;}
.nav{max-width:1180px;margin:0 auto;padding:14px 22px 0;font-size:13px;color:var(--muted);} .nav a{color:var(--accent);text-decoration:none;margin-right:14px;}
.cap{display:flex;gap:6px;margin-top:2px;}
.cap button{font:inherit;font-size:12px;font-weight:600;border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:20px;padding:4px 10px;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,.06);}
"""

VIEWER = """
const GEOM=%s, METRICS=%s;
const COL=GEOM.colors;
let scene,cam,renderer,controls,group,meshes=[],cur="current",colorMode="sh",raf;
function init(){
  const stage=document.getElementById("stage"), w=stage.clientWidth,h=stage.clientHeight;
  scene=new THREE.Scene();
  cam=new THREE.PerspectiveCamera(50,w/h,1,16000); cam.up.set(0,0,1);
  renderer=new THREE.WebGLRenderer({canvas:document.getElementById("cv3d"),antialias:true,preserveDrawingBuffer:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.setSize(w,h); renderer.setClearColor(0xd9e3ea);
  if(THREE.sRGBEncoding!==undefined)renderer.outputEncoding=THREE.sRGBEncoding;
  scene.add(new THREE.HemisphereLight(0xffffff,0xc6d0d3,0.95));
  scene.add(new THREE.AmbientLight(0xffffff,0.42));
  const dl=new THREE.DirectionalLight(0xffffff,0.68); dl.position.set(0.6,-1,1.4); scene.add(dl);
  let minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;
  for(const r of GEOM.recs) for(const p of r.p){minx=Math.min(minx,p[0]);miny=Math.min(miny,p[1]);maxx=Math.max(maxx,p[0]);maxy=Math.max(maxy,p[1]);}
  const cx=(minx+maxx)/2, cy=(miny+maxy)/2, span=Math.max(maxx-minx,maxy-miny);
  group=new THREE.Group(); scene.add(group);
  if(GEOM.sat){const tx=new THREE.TextureLoader().load(GEOM.sat);if(THREE.sRGBEncoding!==undefined)tx.encoding=THREE.sRGBEncoding;
    const se=GEOM.satExtent,gw=se[2]-se[0],gh=se[3]-se[1];
    const gp=new THREE.Mesh(new THREE.PlaneGeometry(gw,gh), new THREE.MeshBasicMaterial({map:tx}));
    gp.position.set((se[0]+se[2])/2,(se[1]+se[3])/2,-0.3); group.add(gp);
  }else{const gp=new THREE.Mesh(new THREE.PlaneGeometry(span*1.6,span*1.6), new THREE.MeshBasicMaterial({color:0xdfe5e7}));gp.position.set(cx,cy,-0.5); group.add(gp);}
  for(const r of GEOM.recs){
    const sh=new THREE.Shape();
    r.p.forEach((pt,i)=> i?sh.lineTo(pt[0],pt[1]):sh.moveTo(pt[0],pt[1]));
    const g=new THREE.ExtrudeGeometry(sh,{depth:1,bevelEnabled:false});
    const m=new THREE.MeshLambertMaterial({color:new THREE.Color(COL[r.sh]||"#999")});
    const mesh=new THREE.Mesh(g,m); mesh.scale.z=r.h[cur]; mesh.userData=r; group.add(mesh); meshes.push(mesh);
  }
  group.position.set(-cx,-cy,0);
  cam.position.set(span*0.55,-span*0.7,span*0.6); controls=new THREE.OrbitControls(cam,renderer.domElement);
  controls.target.set(0,0,40); controls.enableDamping=true; controls.dampingFactor=.08; controls.update();
  window.addEventListener("resize",onresize); animate(); updateMetrics();
}
function onresize(){const st=document.getElementById("stage");cam.aspect=st.clientWidth/st.clientHeight;cam.updateProjectionMatrix();renderer.setSize(st.clientWidth,st.clientHeight);}
function animate(){raf=requestAnimationFrame(animate);
  for(const m of meshes){const t=m.userData.h[cur]; if(Math.abs(m.scale.z-t)>0.3){m.scale.z+=(t-m.scale.z)*0.18;}else m.scale.z=t;}
  controls.update(); renderer.render(scene,cam);
}
function heightColor(hh){const t=Math.max(0,Math.min(1,hh/200));const a=[40,52,68],b=[224,135,99];return new THREE.Color(`rgb(${a[0]+(b[0]-a[0])*t|0},${a[1]+(b[1]-a[1])*t|0},${a[2]+(b[2]-a[2])*t|0})`);}
function applyColor(){for(const m of meshes){const r=m.userData; m.material.color = colorMode==="sh"?new THREE.Color(COL[r.sh]||"#999"):heightColor(r.h[cur]);}}
function setScenario(name){cur=name; if(colorMode==="h")applyColor(); updateMetrics();
  document.querySelectorAll(".scn button").forEach(b=>b.classList.toggle("on",b.dataset.s===name));}
function updateMetrics(){const m=METRICS[cur]||{}; const el=document.getElementById("met");
  el.innerHTML=`<div class="metric"><span>情景</span><b>${cur}</b></div>
  <div class="metric"><span>总 GFA</span><b>×${(m.ratio||1).toFixed(2)}</b></div>
  <div class="metric"><span>平均高</span><b>${(m.mean||0).toFixed(1)} m</b></div>
  <div class="metric"><span>最高</span><b>${(m.max||0).toFixed(0)} m</b></div>`;}
function toggleColor(){colorMode=colorMode==="sh"?"h":"sh"; applyColor();
  document.getElementById("cmode").textContent=colorMode==="sh"?"依持份者":"依高度";}
window.addEventListener("DOMContentLoaded",()=>{
  init();
  document.querySelectorAll(".scn button").forEach(b=>b.onclick=()=>setScenario(b.dataset.s));
  document.getElementById("ctoggle").onclick=toggleColor;
});
let _clay=false;
function _claySet(on){scene.traverse(o=>{if(o.material&&o.material.type==='MeshLambertMaterial'){if(on){if(!o.userData._c)o.userData._c=o.material.color.clone();o.material.color.set(0xccc7c0);}else if(o.userData._c)o.material.color.copy(o.userData._c);}});}
function pfClay(){_clay=!_clay;_claySet(_clay);var b=document.getElementById('claybtn');if(b)b.textContent=_clay?'🎨 分色':'🧱 素模';}
function pfCap(){renderer.render(scene,cam);document.getElementById('cv3d').toBlob(function(bl){var a=document.createElement('a');a.href=URL.createObjectURL(bl);a.download='view_'+cur+'_'+(_clay?'clay':'color')+'.png';a.click();});}
window.addEventListener("DOMContentLoaded",function(){var c=document.getElementById('capbtn');if(c)c.onclick=pfCap;var y=document.getElementById('claybtn');if(y)y.onclick=pfClay;});
"""

HTML = """<!DOCTYPE html><html lang="zh-Hans"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>上海 %s — 本地多源 → 离散权利 → 只调高度 → 3D 新形态</title>
<style>%s</style></head><body>
<div class="nav"><a href="index.html">← 三站对比</a> 陆家嘴 · 曹杨新村 · 豫园</div>
<div class="cover">
  <p class="kick">Urban Stakeholder Workshop · 上海本地多源 → 权利 → 高度 · %s</p>
  <h1>同一座城,只因「谁更有权」而长出不同天际线</h1>
  <p class="lead">先看<b>真实的地方</b>——下面两张是研究范围的真实卫星影像,以及把本地多源 footprint(依离散权利着色)叠上去的「我们的读法」。再往下,是<b>纯查表离散对应 +「只调高度」</b>的互动 3D。建筑高度为 <b>AI 实测</b>;权力来自 EULUC 用途的离散级联查表,转向时<b>不凭空增减总量</b>(总 GFA 守恒,只重分配谁占有它)。</p>
  <div class="sat2">%s%s</div>
</div>
<div class="hero"><div class="inner">
  <p class="lead2">↓ 互动 3D:<b>拖曳旋转、滚轮缩放</b>,按情景钮看天际线此消彼长——footprint 与标签全程不变。</p>
  <div id="stage">
    <canvas id="cv3d"></canvas>
    <div class="hud">
      <div class="scn">%s</div>
      <div class="cap"><button id="capbtn">📷 拍照</button><button id="claybtn">🧱 素模</button></div>
      <div class="card" id="met"></div>
      <div class="card"><div class="toggle">着色:<a id="ctoggle"><span id="cmode">依持份者</span></a></div>
        <div class="legend">%s</div></div>
    </div>
    <div class="hint3d">拖曳=旋转 · 滚轮=缩放 · 右键=平移</div>
  </div>
  <div class="herofoot">3D 由浏览器即时挤出(Three.js,内联);%d 栋真实 footprint;高度为各情景政策套用后之值。零 AI、单档离线。</div>
</div></div>

<div class="wrap">
<h2><span class="num">方法</span>四步:本地多源 → 离散权利 → 高度政策 → 形态</h2>
<p>整条 pipeline 刻意<b>简单、离散、直接</b>:不做语意转换、不算概率,就是「用途→权利」一张<b>级联</b>查表(EULUC→Function→AOI,第一个命中即定)+「只调高度」的情景。权力<b>只</b>来自可编辑的 YAML、<b>不从形态反推</b>。资料:上海 <b>%s</b>,<b>%d 栋</b>本地多源真实 footprint。</p>

<h3 style="margin-top:26px"><span class="num" style="background:#5b86c4">1</span> 看楼:先诚实看原料</h3>
<p>和 OSM 版最大的不同:高度是 <b>AI 实测</b>(非估算),最高 <b>%.0f m</b>、<b>%d 栋 &gt;100m</b>(终于有真高层);用途由面状 <b>EULUC 覆盖 %.0f%%</b>、建筑级 <b>Function %.0f%%</b> 提供——正因 EULUC 是面状全覆盖,unknown 极低(对比 OSM 版的 36%%)。</p>
%s

<h3 style="margin-top:26px"><span class="num" style="background:#7bbf86">2</span> 离散权利:一栋 = 一个 stakeholder</h3>
<p>用 <code>shanghai_lookup.yaml</code> 级联(EULUC 用途类自带 行政办公501 vs 商务办公201 的政商之分 → Function → AOI)把每栋离散对应到唯一权利方。分布:<b>%s</b>;unknown=%d(无用途 join)。<b>informal 恒为空</b>——本数据无非正式信号,不无中生有。改这张表 = 改「谁算谁的」。</p>
<div class="chips">%s</div>
%s

<h3 style="margin-top:26px"><span class="num">3</span> 权力情景:两种模型</h3>
<p>每情景一个 <code>_mode</code>:<b>conserve(默认)</b>= 总 GFA 守恒、权力只<b>重分配</b>(各方权重 <code>mult</code>:&gt;1 多拿、&lt;1 让出,引擎正规化使总量不变);<b>grow</b>= 既有为地板、<b>只增不减</b>(都更新增)。footprint/标签永远不变。本次情景:<b>%s</b>。改 <code>power_scenarios.yaml</code> = 反事实。</p>
%s

<h3 style="margin-top:26px"><span class="num">4</span> 权力如何重分配高度(= 上方 3D 的数据)</h3>
<p>conserve 情景的「总 GFA ×基线」全是 <b>×1.00</b>(守恒);差异全在<b>谁占有</b>——看下表各 stakeholder 平均高、与上方 3D 天际线的此消彼长。只有 grow 情景(都更)才 &gt;1.00。</p>
<table><thead><tr><th>情景</th><th>总 GFA(×基线)</th><th>平均高</th><th>最高</th></tr></thead><tbody>%s</tbody></table>
<table><thead><tr><th>情景</th>%s</tr></thead><tbody>%s</tbody></table>
%s
%s
<p class="teach"><span class="tag">教什么</span>锁死 footprint,总开发量当固定信封(conserve)或地板(grow):<b>总 GFA 守恒时,天际线的此消彼长 100%% 是「谁占有」的重分配,不是凭空增减</b>。学生改 YAML = 亲手做反事实,3D 与数字同步。</p>

<h3 style="margin-top:26px"><span class="num">5</span> 进 Rhino / Grasshopper</h3>
<p>真实 footprint 挤成量体 → <code>out/%s/city_current.obj</code>(%s 顶点)、<code>city_developer_led.obj</code>;<code>buildings_export.csv</code> 给 GH 重建。上方的浏览器 3D 与这些汇出档是同一套几何。</p>

<section class="honest"><h2>诚实边界</h2><ul>
<li><b>高度为 AI 实测但有上限</b>:极端超高层(&gt;~340m,如上海中心/环球金融)可能被低估或缺失;不要把它当测绘。</li>
<li><b>EULUC 为地块(面)级、优先于建筑级 Function</b>:居住地块内零星的学校/诊所会被并入「居民」——简化,非产权考证。</li>
<li><b>danwei 的国家属性看不见</b>:工人新村是国家/单位建的,但用途=居住 → 被算作居民;只有形态记得它是单位建的。这是数据的限制,本身是一课。</li>
<li><b>informal 本数据无信号</b>:恒为空(unknown=%d 是无用途 join,非 informal);不从形态硬猜非正式。</li>
<li><b>AOI 价格/结构仅作离散 tag</b>:为商业 API 代理,不外发原值;「谁的权利」非产权考证。</li>
<li><b>不凭空增减总量</b>:conserve = 总 GFA 守恒、只重分配(既有 = 协商沉淀的固定信封);grow = 只增。footprint 与标签全程不变。</li>
<li><b>零 AI 推断</b>:geopandas/shapely/pandas/matplotlib/pyyaml(+ Three.js 仅前端 3D 着色);无神经网、无语意转换、无生成模型(footprint 的"AI解析"是上游数据来源,本 pipeline 不含 AI)。</li>
</ul></section>
<footer>自含单档 · 3D 由 Three.js 内联即时挤出 · 图 base64 内嵌、数字由 pipeline 实算注入(改 YAML 重跑即同步)· 上海 %s · 教学练习,非真实规划预测</footer>
</div>
<script>%s</script>
<script>%s</script>
<script>%s</script>
</body></html>"""


def operator_section(slug, rows, regs, labels):
    """组装 report 的「进阶:权力算子」HTML 段(注入 honest 段之前)。"""
    order = ["current"] + list(regs.keys())
    head = "".join("<th>%s</th>" % (labels.get(n, "现状")) for n in order)

    def row(key, fmt, title):
        return "<tr><td>%s</td>%s</tr>" % (title, "".join("<td>" + (fmt % rows[n][key]) + "</td>" for n in order))
    body = (row("slender", "%.2f", "瘦长比(塔化↑)") + row("h_cv", "%.2f", "高度CV(集权↑)")
            + row("concentration", "%.2f", "重心集中度(集权↑)") + row("n", "%d", "栋数(细粒↑)"))
    recipe = "".join("<li><b>%s</b>(%s):<code>%s</code></li>" % (
        regs[n]["label"], regs[n]["fingerprint"], " → ".join(st["op"] for st in regs[n]["steps"])) for n in regs)
    return ("""<h2><span class="num">进阶</span>当权力不只改高度:9 个算子 × 4 种权力</h2>
<p>主册「只调高度」只放开一个自由度。但真实的权力改的是<b>形态语法</b>:开发商把板楼拆成细针塔、居民把大院细分成自建小屋、政府把高度向权力重心收拢。
这一节把权力体制写成<b>原子算子的配方</b>(<code>regimes.yaml</code>),四种权力长出四种稳定的<b>形态指纹</b>。详见进阶 notebook 与「算子替换指南」。</p>
<ul>%s</ul>
%s
<p>同一座城市、同一批楼,套四种权力体制——<b>形态差异不是换了数据,纯粹来自「谁更有权、用什么动词」</b>:</p>
%s
<table><thead><tr><th>形态指纹</th>%s</tr></thead><tbody>%s</tbody></table>
<p class="teach"><span class="tag">主要发现</span>四种权力 → 四种<b>形态指纹</b>且跨站稳定:开发商=细针塔(瘦长比飙升);政府=向<b>权力重心</b>收拢的肥峰(重心集中度翻倍);居民自建=细粒碎化(栋数大增);共享=均质开放(高度CV 最低)。
但<b>权力的几何逻辑对基底不变,结果在乎基底</b>:同一种权力盖在里弄和 CBD 不会长成一样——权力 × 在地是对话,不是盖章。</p>""" % (
        recipe,
        fig_block(slug, "regimes.png", "图:现状 + 四种权力体制(同高度色阶可横比)— 四种形态指纹"),
        fig_block(slug, "fingerprints.png", "图:四种权力的形态指纹(measure.py 量化:瘦长比 / 高度CV / 重心集中 / 栋数)"),
        head, body))


def build_report(slug):
    traditionalize_engine_labels()                 # 交付物繁体:图内文字也转繁(只影响本报告进程)
    df, scen, H = load(slug)
    s = compute_stats(slug, df, scen, H)
    try:
        fig_satellite(slug, df, s)                 # 需联网(Esri 卫星);离线则跳过,报告其余部分照常
    except Exception as e:
        print("  卫星跳过(没网或缺 contextily):", e)
    fig_step1(slug, df, s)
    fig_step2(slug, df, s)
    fig_step3(slug, df, scen, H, s)
    fig_step4(slug, scen, s)
    fig_scenarios_3d(slug, df, scen, H, s)
    op_rows, op_regs, op_labels = fig_operators(slug, df, s)
    export_obj(slug, df, scen, H, s)
    _bx = _footprint_bounds(df)
    _sat, _sext = C.site_ground(_bx[0], _bx[1], _bx[2], _bx[3], slug)
    geom = build_geometry(df, scen, H, _sat, _sext)
    n_recs = len(json.loads(geom)["recs"])
    three = (WEB / "three.min.js").read_text(encoding="utf-8")
    orbit = (WEB / "OrbitControls.js").read_text(encoding="utf-8")
    metrics = {k: {"ratio": s["rows"][k]["ratio"], "mean": s["rows"][k]["mean"], "max": s["rows"][k]["max"]} for k in s["scen"]}
    viewer = VIEWER % (geom, json.dumps(metrics))
    place = s["name"]

    present = [sh for sh in SH_ORDER if s["dist"].get(sh, 0)]
    dist_txt = "、".join("%s %d" % (C.SH_LABEL[sh].split("(")[0], s["dist"].get(sh, 0)) for sh in present)
    chips = " ".join('<span class="chip"><span class="dot" style="background:%s"></span>%s</span>' % (C.SH_COLOR[sh], C.SH_LABEL[sh]) for sh in SH_ORDER)
    legend = " ".join('<span><i style="background:%s"></i>%s</span>' % (C.SH_COLOR[sh], C.SH_LABEL[sh].split("(")[0]) for sh in SH_ORDER)
    scn_btns = "".join('<button data-s="%s"%s>%s</button>' % (k, ' class="on"' if k == "current" else "", k) for k in s["scen"])
    gfa_rows = "".join("<tr><td>%s</td><td>×%.2f</td><td>%.1f m</td><td>%.0f m</td></tr>" % (
        k + ("(基线)" if k == "current" else ""), s["rows"][k]["ratio"], s["rows"][k]["mean"], s["rows"][k]["max"]) for k in s["scen"])
    sh_head = "".join("<th>%s</th>" % C.SH_LABEL[sh].split("(")[0] for sh in present)
    sh_rows = "".join("<tr><td>%s</td>%s</tr>" % (k, "".join("<td>%.1f</td>" % s["sh_h"][k][sh] for sh in present)) for k in s["scen"])

    html = HTML % (
        place, CSS, place,
        fig_block(slug, "satellite.png", "真实卫星(Esri World Imagery)— 上海 %s" % place),
        fig_block(slug, "satellite_overlay.png", "卫星 + 本地多源 footprint(依离散权利着色)= 真实地方 vs 我们的读法"),
        scn_btns, legend, n_recs,
        place, s["n"],
        s["h_max"], s["n_gt100"], s["cov"]["euluc"] * 100, s["cov"]["function"] * 100,
        fig_block(slug, "step1_buildings.png", "图:%d 栋真实 footprint(AI 实测高度,尚未贴权力)" % s["n"]),
        dist_txt, s["dist"].get("unknown", 0), chips,
        fig_block(slug, "step2_stakeholders.png", "图:离散 stakeholder 着色 + 栋数/GFA 占比"),
        "、".join(s["scen"]),
        fig_block(slug, "step3_policies.png", "图:高度政策热图(红=拔高/蓝=压低)"),
        gfa_rows, sh_head, sh_rows,
        fig_block(slug, "step4_metrics.png", "图:各情景指标对照(总 GFA、平均高、最高)"),
        fig_block(slug, "scenarios_3d.png", "静态 3D 对比(同视角):权力重分配 → 天际线此消彼长,总 GFA 守恒(可截图/放投影片)"),
        slug, "{:,}".format(s["obj"][1]),
        s["dist"].get("unknown", 0), place,
        three, orbit, viewer)

    # 注入「进阶:权力算子」段(在诚实边界之前),再整体转繁体
    html = html.replace('<section class="honest">', operator_section(slug, op_rows, op_regs, op_labels) + '\n<section class="honest">')
    html = html.replace('lang="zh-Hans"', 'lang="zh-Hant"')
    html = _zh_hant(html)

    rp = OUT / slug / "report.html"
    rp.write_text(html, encoding="utf-8")
    print("写了:", rp, "| %.2f MB | %d 栋 | %d 图" % (
        rp.stat().st_size / 1e6, n_recs, html.count("data:image/png;base64,")))
    try:                                  # 更新 out/manifest.json,web/index.html 即读到本站最新统计
        import manifest
        manifest.set_report(slug, s["n"], s["h_max"], s["dist"].get("unknown", 0) / s["n"] * 100)
    except Exception as e:
        print("  manifest skip:", e)
    return s


def build_index(sites):
    cards = ""
    for slug, name, role, s in sites:
        cards += ('<div class="sc"><b>%s</b><span>%s</span>'
                  '<small>%d 栋 · 最高 %.0fm · unknown %.0f%%</small>'
                  '<div class="lk"><a href="%s/report.html">打开报告 → 只调高度 + 进阶权力算子</a></div></div>') % (
            name, role, s["n"], s["h_max"], s["dist"].get("unknown", 0) / s["n"] * 100, slug)
    html = """<!DOCTYPE html><html lang="zh-Hans"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>上海三站 — 权力 → 形态</title>
<style>%s
.grid{max-width:1080px;margin:20px auto;padding:0 22px;display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
@media(max-width:760px){.grid{grid-template-columns:1fr;}}
.sc{display:flex;flex-direction:column;gap:4px;border:1px solid var(--line);border-radius:12px;padding:18px;color:var(--ink);background:#fff;box-shadow:0 1px 6px rgba(0,0,0,.05);}
.sc b{font-size:18px;color:var(--accent);} .sc span{font-size:13px;color:#3a4347;} .sc small{font-size:12px;color:var(--muted);margin-top:4px;}
.sc .lk{display:flex;flex-direction:column;gap:6px;margin-top:12px;} .sc .lk a{font-size:13px;color:var(--accent);text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:7px 11px;background:#f5faf9;}
.sc .lk a:hover{background:#e8f3f2;}
</style></head><body>
<div class="cover"><p class="kick">Urban Stakeholder Workshop · 上海本地多源</p>
<h1>同一座城,三种权力,三种天际线</h1>
<p class="lead">同一套方法(本地多源真实数据 → 用途的离散级联查表 → 只调高度的 conserve/grow 情景),跑上海三个形态家族的代表街道。每站点开互动 3D + 卫星 + 静态对比。</p></div>
<div class="grid">%s</div>
<div class="wrap"><p style="color:#717b80;font-size:13px;margin-top:24px">数据:上海城市数据集(AI建筑-实测高度 / EULUC用途 / 带年份Function / 百度AOI)。零 AI 推断。informal 本数据无信号、恒空。选点见 shanghai_probe.md。</p></div>
</body></html>""" % (CSS, cards)
    html = html.replace('lang="zh-Hans"', 'lang="zh-Hant"')
    (OUT / "index.html").write_text(_zh_hant(html), encoding="utf-8")
    print("写了:", OUT / "index.html")


_BY = {s["slug"]: s for s in config.SITES}
SITES = [(sl, _BY[sl]["name"], _BY[sl]["family"]) for sl in config.REPORT_SITES]   # 默认 3 站:陆家嘴/曹杨/豫园

if __name__ == "__main__":
    if len(sys.argv) > 1:
        build_report(sys.argv[1])
    else:
        done = []
        for slug, name, role in SITES:
            print("\n=== %s (%s) ===" % (name, slug))
            s = build_report(slug)
            done.append((slug, name, role, s))
        build_index(done)
        print("\n全部完成。")

