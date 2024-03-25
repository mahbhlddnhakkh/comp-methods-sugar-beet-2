import dearpygui.dearpygui as dpg
from src.config import CFG
if (__name__ == "__main__"):
    dpg.create_context()
from src.gui import create_gui

def main():
    with dpg.font_registry():
        with dpg.font("fonts/notomono-regular.ttf", 15, default_font=True) as font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
    with dpg.window() as window:
        if (CFG.debug):
            with dpg.menu_bar():
                with dpg.menu(label="Debug Tools"):
                    dpg.add_menu_item(label="Show About", callback=lambda: dpg.show_tool(dpg.mvTool_About))
                    dpg.add_menu_item(label="Show Metrics", callback=lambda: dpg.show_tool(dpg.mvTool_Metrics))
                    dpg.add_menu_item(label="Show Documentation", callback=lambda: dpg.show_tool(dpg.mvTool_Doc))
                    dpg.add_menu_item(label="Show Debug", callback=lambda: dpg.show_tool(dpg.mvTool_Debug))
                    dpg.add_menu_item(label="Show Style Editor", callback=lambda: dpg.show_tool(dpg.mvTool_Style))
                    dpg.add_menu_item(label="Show Font Manager", callback=lambda: dpg.show_tool(dpg.mvTool_Font))
                    dpg.add_menu_item(label="Show Item Registry", callback=lambda: dpg.show_tool(dpg.mvTool_ItemRegistry))
        create_gui()
    dpg.bind_font(font)
    dpg.create_viewport(title='comp-methods-sugar-beet-gui', width=1400, height=800, min_width=1080, min_height=500)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(window, True)
    dpg.start_dearpygui()
    dpg.destroy_context()

if (__name__ == "__main__"):
    main()