import dearpygui.dearpygui as dpg
from src.user_config import algs
from src.util import work_prop
from src.config import float_precision_str, CFG
from src.themes import dpg_plot_line_themes, dpg_plot_line_names, markers_count, highlight_cell_theme
from typing import List, Dict, List
import numpy as np
import os
import csv
import math

def dpg_add_input(dtype=str, **kwargs):
    '''
    dpg.add_input_*** but looks for type from argument
    float -> double because why not?
    '''
    if (dtype is int):
        return dpg.add_input_int(**kwargs)
    elif (dtype is float):
        return dpg.add_input_double(**kwargs)
    elif (dtype is str):
        return dpg.add_input_text(**kwargs)

def center_pos_popup(_popup):
    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()
    width = dpg.get_item_width(_popup)
    height = dpg.get_item_height(_popup)
    dpg.set_item_pos(_popup, [viewport_width // 2 - width // 2, viewport_height // 2 - height // 2])

def dpg_add_separator():
    '''
    This separator sometimes looks better than dpg.add_separator()
    '''
    dpg.add_text("")
    dpg.add_separator()

def dpg_get_values(items):
    '''
    Useful when unsure if argument is list or single value
    '''
    if (type(items) is list or type(items) is tuple):
        return dpg.get_values(items)
    else:
        return dpg.get_value(items)

class select_algs:
    '''
    Creates buttons and interface for selecting algorithms and their parameters
    '''
    # https://github.com/hoffstadt/DearPyGui/issues/1513
    _algs_group = None
    _selected_algs = None
    _params = None
    _exp_res = None
    _params_launched_once = None
    _checkbox_default_value = None

    def __init__(self, exp_res=None):
        self._exp_res = exp_res
        self._selected_algs = [True]*len(algs)
        for i in range(len(algs)):
            if ("check_default" in algs[i]):
                self._selected_algs[i] = algs[i]["check_default"]
            if ("hidden" in algs[i] and algs[i]["hidden"]):
                self._selected_algs[i] = False
        self.run_default_params()
        self._params_launched_once = False
        self._algs_group = dpg.add_group(horizontal=True)
        self._checkbox_default_value = False
        dpg.add_button(label="Выбрать алгоритмы", parent=self._algs_group, callback=self.create_select_algs_popup)
        dpg.add_button(label="Выбрать параметры алгоритмов", parent=self._algs_group, callback=self.create_select_params_popup)
        dpg.add_checkbox(label="Параметры алгоритмов по умолчанию", parent=self._algs_group, user_data=dpg.last_item(), callback=self.checkbox_always_default_callback, default_value=True)
        self.checkbox_always_default_callback(dpg.last_item(), dpg.get_value(dpg.last_item()), dpg.get_item_user_data(dpg.last_item()))
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Некоторые параметры по умолчанию зависят от n, mu или других. Используйте, чтобы зависимости 'подтягивалось' за параметрами автоматически.")
            dpg.add_text("При включении блокируется выбор параметров алгоритмов")
        self.set_exp_res()

    def checkbox_always_default_callback(self, sender, app_data, user_data):
        if (app_data):
            self._checkbox_default_value = True
            dpg.configure_item(user_data, enabled=False)
        else:
            self._checkbox_default_value = False
            dpg.configure_item(user_data, enabled=True)

    def create_select_algs_popup(self):
        with dpg.window(label="Выбрать алгоритмы", modal=True, no_close=True) as popup:
            with dpg.group():
                for i in range(len(algs)):
                    if (not ("hidden" in algs[i] and algs[i]["hidden"])):
                        dpg.add_checkbox(label=algs[i]["name"], default_value=self._selected_algs[i])
            with dpg.group(horizontal=True):
                dpg.add_button(label="ОК", user_data=(popup,), callback=lambda sender, app_data, user_data: self.on_ok_select_algs(user_data[0]))
                dpg.add_button(label="Отмена", user_data=(popup,), callback=lambda sender, app_data, user_data: self.on_close_popup(user_data[0]))
            center_pos_popup(popup)

    def create_select_params_popup(self):
        self._params_launched_once = True
        with dpg.window(label="Выбрать параметры алгоритмов", modal=True, no_close=True) as popup:
            self.generate_params_on_popup(popup)
    
    def generate_params_on_popup(self, popup, do_center=True):

        def default_all_btn_callback(self, _popup):
            self.run_default_params()
            dpg.delete_item(_popup, children_only=True)
            dpg.push_container_stack(_popup)
            self.generate_params_on_popup(_popup, False)
            dpg.pop_container_stack()
        done_once = False
        tmp_btn = dpg.add_button(label="Все по умолчанию", user_data=popup, callback=lambda sender, app_data, user_data: default_all_btn_callback(self, user_data))
        with dpg.group():
            for i in self._params:
                if (self._selected_algs[i]):
                    done_once = True
                    with dpg.group(user_data=i):
                        dpg.add_text(algs[i]["name"])
                        for j in range(len(algs[i]["params"])):
                            p = algs[i]["params"][j]
                            with dpg.group(horizontal=True, user_data=j):
                                dpg.add_text(p["name"])
                                dpg_add_input(p["type"], default_value=self._params[i][j], width=150)
                                dpg.add_button(label="По умолчанию", user_data=(dpg.last_item(), p["default"]), callback=lambda sender, app_data, user_data: dpg.set_value(user_data[0], user_data[1](self._exp_res)))
        if (not done_once):
            dpg.add_text("Параметры алгоритмов не найдены")
            dpg.configure_item(tmp_btn, show=False)
        with dpg.group(horizontal=True):
            if (done_once):
                dpg.add_button(label="ОК", user_data=(popup,), callback=lambda sender, app_data, user_data: self.on_ok_select_params(user_data[0]))
            dpg.add_button(label="Отмена", user_data=(popup,), callback=lambda sender, app_data, user_data: self.on_close_popup(user_data[0]))
        if (do_center):
            center_pos_popup(popup)

    def on_ok_select_algs(self, _popup):
        checkboxes = dpg.get_item_children(dpg.get_item_children(_popup)[1][0])[1]
        self._selected_algs = dpg.get_values(checkboxes)
        self.set_exp_res()
        self.on_close_popup(_popup)

    def on_ok_select_params(self, _popup):
        params_groups = dpg.get_item_children(dpg.get_item_children(_popup)[1][1])[1]
        for a in params_groups:
            i = dpg.get_item_user_data(a)
            param_group = dpg.get_item_children(a)[1][1:]
            for p in param_group:
                j = dpg.get_item_user_data(p)
                p_value = dpg.get_value(dpg.get_item_children(p)[1][1])
                self._params[i][j] = p_value
        self.set_exp_res()
        self.on_close_popup(_popup)

    def on_close_popup(self, _popup):
        dpg.delete_item(_popup)

    def set_exp_res(self):
        self._exp_res.chosen_algs = self._selected_algs
        self._exp_res.params_algs_specials = self._params

    def run_default_params(self):
        self._params = {}
        for i in range(len(algs)):
            if ("params" in algs[i]):
                self._params[i] = []
                for p in algs[i]["params"]:
                    self._params[i].append(p["default"](self._exp_res))
        self.set_exp_res()
    
    def run_default_if_params_popup_not_opened(self):
        if (not self._params_launched_once or self._checkbox_default_value):
            self.run_default_params()

def save_table_as_csv(work, tb, _save_path=None, _ignored_columns=None):
    '''
    Saves table as csv for whatever reason
    '''
    tb_ch = dpg.get_item_children(tb)
    ignored_columns = None
    if (_ignored_columns != None):
        ignored_columns = sorted(_ignored_columns, reverse=True)
    if (ignored_columns != None):
        for i in ignored_columns:
            del tb_ch[0][i]
    save_path = _save_path
    if (save_path == None):
        dpg.lock_mutex()
        save_path = filedialog.asksaveasfilename(filetypes=[("Таблица", "*.csv")], initialdir=work.working_directory)
        dpg.unlock_mutex()
    if (save_path == "" or save_path == ()):
        return
    with open(save_path, 'w', encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";", lineterminator="\r\n")
        first_row = []
        for e in tb_ch[0]:
            first_row.append(dpg.get_item_label(e))
        writer.writerow(first_row)
        for e in tb_ch[1]:
            r_ch = dpg.get_item_children(e)[1]
            if (ignored_columns != None):
                for i in ignored_columns:
                    del r_ch[i]
            writer.writerow([dpg.get_value(ee).strip() for ee in r_ch])

def generate_result_table_columns(tb):
    '''
    Generates result table's columns
    '''
    dpg.add_table_column(label="Эксперимент")
    dpg.add_table_column(label="Параметры", parent=tb)
    dpg.add_table_column(label="n", parent=tb, init_width_or_weight=0.15)
    dpg.add_table_column(label="Параметры алгоритмов", parent=tb)
    for i in range(len(algs)):
        dpg.add_table_column(label=algs[i]["name"] + " (S / Error)", parent=tb, init_width_or_weight=0.4)

def generate_result_table_row(exp_res, tb):
    '''
    Generates result table's row from exp_res
    '''
    with dpg.table_row(parent=tb, user_data=exp_res) as r:
        dpg.add_text(exp_res.exp_name + f"\nКол-во экспериментов: {exp_res.exp_count}")
        tmp = ""
        for key in exp_res.params.keys():
            p = exp_res.params[key]
            tmp += key
            if (p == None):
                tmp += "\n"
                continue
            tmp += " = "
            if (type(p) is tuple or type(p) is list):
                if (p[2] != 0):
                    tmp += "("
                else:
                    tmp += "["
                tmp += f'{p[0]}, {p[1]}'
                if (p[3] != 0):
                    tmp += ")"
                else:
                    tmp += "]"
            else:
                tmp += str(p)
            tmp += "\n"
        tmp = tmp[:len(tmp)-1]
        dpg.add_text(tmp)
        dpg.add_text(str(exp_res.n))
        tmp = ""
        for e in exp_res.params_algs_specials:
            if (exp_res.chosen_algs[e]):
                tmp += algs[e]["name"] + ":\n"
                cur_params = algs[e]["params"]
                for ee in range(len(cur_params)):
                    tmp += cur_params[ee]["name"] + " = " + str(exp_res.params_algs_specials[e][ee]) + '\n'
        dpg.add_text(tmp)
        best_alg_max = 0.0
        best_alg = 0
        for i in range(len(algs)):
            if (exp_res.chosen_algs[i]):
                dpg.add_input_text(default_value=float_precision_str % exp_res.phase_averages[i][-1] + "\n" + float_precision_str % exp_res.average_error[i], width=-1, readonly=True, multiline=True)
                #dpg.add_text(float_precision_str % exp_res.phase_averages[i][-1] + "\n" + float_precision_str % exp_res.average_error[i])
                if (best_alg_max < exp_res.phase_averages[i][-1] and i != 0):
                    best_alg = i
                    best_alg_max = exp_res.phase_averages[i][-1]
            else:
                dpg.add_text("")
        if (best_alg != 0):
            r_children = dpg.get_item_children(r, 1)
            dpg.bind_item_theme(r_children[len(r_children)-len(algs)+best_alg], highlight_cell_theme)
    return r

def generate_result_plot(exp_res, add_save_button=True, add_edit_size_button=True, legend_outside=True):
    '''
    Generates result plot from exp_res
    '''

    def resize_plot_width(sender, app_data, user_data):
        '''
        Sets plot width from input
        '''
        dpg.configure_item(user_data, width=app_data)

    def resize_plot_height(sender, app_data, user_data):
        '''
        Sets plot width from input
        '''
        dpg.configure_item(user_data, height=app_data)

    # TODO: good height for plot?
    dpg_plot_size = (-1, math.floor(dpg.get_viewport_width()/3))
    with dpg.plot(label=CFG.plot_title + '\n' + exp_res.exp_name, width=dpg_plot_size[0], height=dpg_plot_size[1], anti_aliased=True) as dpg_plot:
        if (legend_outside):
            dpg.add_plot_legend(outside=True, location=dpg.mvPlot_Location_East)
        else:
            dpg.add_plot_legend()
        x = dpg.add_plot_axis(dpg.mvXAxis, label=CFG.plot_x_label)
        y = dpg.add_plot_axis(dpg.mvYAxis, label=CFG.plot_y_label)
        x_arr = np.arange(1, exp_res.n+1, dtype=int)
        j = 0
        for i in range(len(algs)):
            if (exp_res.chosen_algs[i]):
                j_c = j % markers_count
                #dpg.bind_item_theme(dpg.add_line_series(x_arr, exp_res.phase_averages[i], label=f'{algs[i]["name"]} [{dpg_plot_line_names[j_c]}]', parent=y), dpg_plot_line_themes[j_c])
                dpg.bind_item_theme(dpg.add_line_series(x_arr, exp_res.phase_averages[i], label=f'{algs[i]["name"]}', parent=y), dpg_plot_line_themes[j_c])
                j += 1
    if (add_edit_size_button):
        with dpg.group(horizontal=True):
            dpg.add_text("Ширина: ")
            dpg.add_input_int(min_value=-1, min_clamped=True, step=0, user_data=dpg_plot, callback=resize_plot_width, default_value=dpg_plot_size[0], on_enter=True, width=50)
            dpg.add_text("Высота: ")
            dpg.add_input_int(min_value=-1, min_clamped=True, step=0, user_data=dpg_plot, callback=resize_plot_height, default_value=dpg_plot_size[1], on_enter=True, width=50)
    #if (add_save_button):
        #dpg.add_button(label="Сохранить график", user_data=(exp_res, None), callback=lambda sender, app_data, user_data: download_plot_matplotlib(*user_data))
    return dpg_plot

def generate_result_plot_table(work: work_prop) -> tuple:
    '''
    Generates results and plot table
    '''
    with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=True, policy=dpg.mvTable_SizingStretchProp) as tb:
        generate_result_table_columns(tb)
        for exp in work.exp_res:
            generate_result_table_row(exp, tb)
    dpg.add_button(label="Сохранить таблицу (csv)", user_data=(work, tb, None), callback=lambda sender, app_data, user_data: save_table_as_csv(*user_data))
    dpg.add_text("")
    for exp in work.exp_res:
        dpg_plot = generate_result_plot(exp, True, True)
        dpg.add_text("")
    return (tb, dpg_plot)

def generate_input_for_exp(param, default=None):
    '''
    Generates input for experiment params
    '''

    def generate_input_range(param, default) -> tuple:
        '''
        Generates input with special 'range'
        E.g. to type range for a_i
        Return tuple of 2 dpg inputs: min and max
        '''
        def manage_range(sender, app_data, user_data):
            param = user_data[2]
            if (user_data[0] and ("range_min" in param and param["range_min"]["type"] != "include" and app_data <= param["range_min"]["min"] or "range_max" in param and param["range_max"]["type"] != "include" and app_data >= param["range_max"]["max"])):
                # left
                dpg.set_value(user_data[1], "(")
            elif (user_data[0]):
                dpg.set_value(user_data[1], "[")
            if (not user_data[0] and ("range_max" in param and param["range_max"]["type"] != "include" and app_data >= param["range_max"]["max"] or "range_min" in param and param["range_min"]["type"] != "include" and app_data <= param["range_min"]["min"])):
                # right
                dpg.set_value(user_data[1], ")")
            elif (not user_data[0]):
                dpg.set_value(user_data[1], "]")

        res = [None, None]
        range_text = "Диапазон: "
        bracket_left = dpg.add_text("[")
        kwargs = ({}, {})
        if ("range_min" in param):
            kwargs[0]["default_value"] = param["range_min"]["min"]
            kwargs[1]["default_value"] = param["range_min"]["min"]
            kwargs[0]["min_value"] = param["range_min"]["min"]
            kwargs[0]["min_clamped"] = True
            kwargs[1]["min_value"] = param["range_min"]["min"]
            kwargs[1]["min_clamped"] = True
            if (param["range_min"]["type"] == "include"):
                range_text += "["
            else:
                range_text += "("
            range_text += f'{param["range_min"]["min"]}'
        else:
            range_text += "(inf"
        range_text += ", "
        if ("range_max" in param):
            kwargs[1]["default_value"] = param["range_max"]["max"]
            kwargs[1]["max_value"] = param["range_max"]["max"]
            kwargs[1]["max_clamped"] = True
            kwargs[0]["max_value"] = param["range_max"]["max"]
            kwargs[0]["max_clamped"] = True
            range_text += f'{param["range_max"]["max"]}'
            if (param["range_max"]["type"] == "include"):
                range_text += "]"
            else:
                range_text += ")"
        else:
            range_text += "inf)"
        if (default != None):
            kwargs[0]["default_value"] = default[0]
            kwargs[1]["default_value"] = default[1]
        res[0] = dpg_add_input(param["type"], user_data=(True, bracket_left, param), width=100, step=0, callback=manage_range, **(kwargs[0]))
        dpg.add_text(",")
        bracket_right = dpg.add_text("]")
        res[1] = dpg_add_input(param["type"], user_data=(False, bracket_right, param), width=100, step=0, callback=manage_range, before=bracket_right, **(kwargs[1]))
        dpg.add_text("")
        dpg.add_text(range_text)
        for e in res:
            manage_range(e, dpg.get_value(e), dpg.get_item_user_data(e))
        return res

    if ("special" in param and "special" == "empty"):
        return None
    res = None
    with dpg.group(horizontal=True):
        if (not "special" in param):
            kwargs = {}
            if ("max" in param):
                kwargs["max_value"] = param["max"]
                kwargs["max_clamped"] = True
                kwargs["default_value"] = param["max"]
            if ("min" in param):
                kwargs["min_value"] = param["min"]
                kwargs["min_clamped"] = True
                kwargs["default_value"] = param["min"]
            if ("default" in param):
                kwargs["default_value"] = param["default"]
            if (default != None):
                kwargs["default_value"] = default
            dpg.add_text(param["title"])
            with dpg.tooltip(dpg.last_item()):
                dpg.add_text(param["name"])
            res = dpg_add_input(param["type"], **kwargs)
        else:
            if (param["special"] == "range"):
                dpg.add_text(param["title"])
                with dpg.tooltip(dpg.last_item()):
                    dpg.add_text(param["name"])
                res = generate_input_range(param, default)
    if (res != None):
        param["dpg"] = res
    return res

def fix_range_min_max_input_exp(params: List[dict]):
    '''
    Fixes incorrect range parameters.
    When min > max, we just swap them. 
    '''
    for p in params:
        if (p.get("special") == "range" and "dpg" in p):
            vals = dpg.get_values(p["dpg"])
            if (vals[0] > vals[1]):
                dpg.set_value(p["dpg"][0], vals[1])
                dpg.set_value(p["dpg"][1], vals[0])
                for e in p["dpg"]:
                    dpg.get_item_configuration(e)["callback"](e, dpg.get_value(e), dpg.get_item_user_data(e))
