import dearpygui.dearpygui as dpg

with dpg.theme() as highlight_cell_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (2, 48, 32, 255))

# TODO: what about filled and open markers? It will be +7 additional markers. Don't know how to use marker name in plot legend in that case though.
# https://matplotlib.org/3.2.2/gallery/lines_bars_and_markers/marker_fillstyle_reference.html <- simple
# In dpg it seems possible to have open markers https://raw.githubusercontent.com/wiki/epezent/implot/screenshots3/markers.gif
# but I can't find a way to do it from documentation https://dearpygui.readthedocs.io/en/latest/documentation/themes.html#plot-markers .
dpg_plot_line_themes = []
for marker in (
        dpg.mvPlotMarker_Circle, dpg.mvPlotMarker_Square, dpg.mvPlotMarker_Diamond, dpg.mvPlotMarker_Up, dpg.mvPlotMarker_Down, dpg.mvPlotMarker_Left, dpg.mvPlotMarker_Right, dpg.mvPlotMarker_Cross, dpg.mvPlotMarker_Plus, dpg.mvPlotMarker_Asterisk
    ):
    with dpg.theme() as tmp_line_theme:
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, marker, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 5, category=dpg.mvThemeCat_Plots)
    dpg_plot_line_themes.append(tmp_line_theme)

# dpg can't have marker along side with line color in plot legend unlike plt. Too bad! The solution is to use "{alg} [{marker}]" in plot legend.
dpg_plot_line_names = [
    "круг", "квадрат", "ромб", "вверх", "вниз", "влево", "вправо", "крест", "плюс", "звезда"
]

plt_markers = ["o", "s", "D", "^", "v", "<", ">", "x", "+", (6, 2, 0)]

markers_count = len(dpg_plot_line_themes) # 10, enough for 6 algorithms tho
