"""
engine/plots — 所有繪圖(view 層)。notebook 只 import 這一個。
=================================================================
分工:
  common.py = model(算):載資料 / 貼角色 / 算高度 / 擠 OBJ。
  plots/    = view(畫):每個 step 一個圖檔,共用核心在 _base。
  notebook  = controller(串):算交給 common,畫交給 plots,自己只負責組合。

契約:plot func 只收「已算好的」df / heights / scenarios,不重算、不讀檔。

用法(notebook):
  import plots
  plots.data_overview(df)
  plots.power_map(df)
  plots.policy_heatmap(scenarios)
  plots.skyline_panels(df, heights);  plots.metrics(df, heights)
  plots.city_3d(sub);                 plots.city_3d_plotly(sub)
"""
from ._base import (SH_COLOR, SH_LABEL, HEIGHT_CMAP,
                    sh_color, sh_label, stakeholder_order, safeplot,
                    plot_footprints, legend_below, height_norm, footer, save_fig,
                    origin_of, building_faces)
from .step1_data import data_overview
from .step2_power import power_map
from .step3_policy import policy_heatmap
from .step4_form import skyline_panels, metrics
from .step5_3d import city_3d, city_3d_plotly

__all__ = [
    "SH_COLOR", "SH_LABEL", "HEIGHT_CMAP",
    "sh_color", "sh_label", "stakeholder_order", "safeplot",
    "plot_footprints", "legend_below", "height_norm", "footer", "save_fig",
    "origin_of", "building_faces",
    "data_overview", "power_map", "policy_heatmap",
    "skyline_panels", "metrics", "city_3d", "city_3d_plotly",
]
