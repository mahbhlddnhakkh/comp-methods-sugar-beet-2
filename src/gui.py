import dearpygui.dearpygui as dpg
from src.gui_util import generate_input_for_exp, select_algs, fix_range_min_max_input_exp, generate_result_plot_table
#from src.config import CFG, float_precision
from src.util import exp_res_props, work_prop, convert_to_p_matrix
from src.experiment import do_experiment
from src.user_config import algs, exp_modes, exp_modes_func
from tkinter import filedialog
import sys
import os
import copy

exp_modes_keys = tuple(list(exp_modes.keys()).copy())
exp_modes = (copy.deepcopy(exp_modes), copy.deepcopy(exp_modes))
last_exp_mode = [1, 1]

def create_gui():
    '''
    Creates gui
    '''
    def choose_working_directory_callback(_path = None):
        '''
        Chooses current working directory (to automatically save things)
        '''
        tmp = _path
        if (tmp == None):
            dpg.lock_mutex()
            tmp = filedialog.askdirectory(initialdir=work.working_directory)
            dpg.unlock_mutex()
        if (tmp == "" or tmp == ()):
            return
        work.working_directory = tmp
        dpg.set_value(working_directory_input, work.working_directory)

    def choose_from_file_btn_callback():
        '''
        Button "Выбрать из файла"
        '''
        dpg.lock_mutex()
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("Любые", "*.*")], initialdir=work.working_directory)
        dpg.unlock_mutex()
        if (path == "" or path == ()):
            return
        work.get_from_file(path)
        choose_working_directory_callback(os.path.dirname(path))
        dpg.delete_item(res_group, children_only=True)
        dpg.set_value(n_input, work.exp_res[0].n)
        dpg.delete_item(parameters_table, children_only=True)
        construct_parameters_table(parameters_table)
        if (work.exp_res[0].average_error != None):
            calc_btn_callback(False)

    def set_n(sender, app_data):
        '''
        As name implies, sets exp_res n
        '''
        for exp in work.exp_res:
            exp.n = app_data

    def construct_parameters_table_cell_i(i, use_default=True):
        '''
        Constructs cell for table
        '''
        dpg.add_text(exp_names[i])
        work.exp_res[i].exp_name = exp_names[i]
        with dpg.group(horizontal=True):
            dpg.add_text("Количество экспериментов")
            exp_count_inputs[i] = dpg.add_input_int(min_value=1, default_value=1, min_clamped=True)
        with dpg.group(horizontal=True):
            dpg.add_text("Режим")
            mode_radio_btn = dpg.add_radio_button(items=exp_modes_keys, horizontal=True, user_data=i, callback=switch_mode)
        mode_groups.append(tuple([dpg.add_group(show=False) for key in exp_modes_keys]))
        for j in range(len(mode_groups[i])):
            cur_exp_mode = work.exp_res[i].exp_mode == j
            key = exp_modes_keys[j]
            params = exp_modes[i][key]
            dpg.push_container_stack(mode_groups[i][j])
            for p in params:
                default = None
                if (use_default and cur_exp_mode and work.exp_res[i].params != None):
                    default = work.exp_res[i].params[p["name"]]
                generate_input_for_exp(p, default)
            dpg.pop_container_stack()
        dpg.set_value(mode_radio_btn, exp_modes_keys[work.exp_res[i].exp_mode])
        switch_mode(mode_radio_btn, exp_modes_keys[work.exp_res[i].exp_mode], i)

    def construct_parameters_table(table):
        '''
        Constructs parameters table for P and P0
        '''
        mode_groups.clear()
        dpg.push_container_stack(table)
        dpg.add_table_column()
        dpg.add_table_column()
        with dpg.table_row():
            for i in range(2):
                with dpg.table_cell():
                    construct_parameters_table_cell_i(i)
        dpg.pop_container_stack()

    def switch_mode(sender, app_data, user_data):
        '''
        Switches "Без дозаривания" / "С дозариванием"
        '''
        global last_exp_mode
        dpg.configure_item(mode_groups[user_data][last_exp_mode[user_data]], show=False)
        last_exp_mode[user_data] = exp_modes_keys.index(app_data)
        dpg.configure_item(mode_groups[user_data][last_exp_mode[user_data]], show=True)

    def fill_exp_res():
        '''
        As name implies, fill out exp_res_props from inputs
        '''
        for i in range(2):
            cur_exp_mode = exp_modes_keys[last_exp_mode[i]]
            fix_range_min_max_input_exp(exp_modes[i][cur_exp_mode])
            exp_res = work.exp_res[i]
            exp_res.n = dpg.get_value(n_input)
            exp_res.exp_count = dpg.get_value(exp_count_inputs[i])
            exp_res.exp_mode = last_exp_mode[i]
            exp_res.params = {}
            for p in exp_modes[i][cur_exp_mode]:
                if ("special" in p):
                    if (p["special"] == "empty"):
                        exp_res.params[p["name"]] = None
                    elif (p["special"] == "range"):
                        tmp = [None]*4
                        tmp[:2] = dpg.get_values(p["dpg"])
                        brackets = "()"
                        for i in range(2):
                            tmp[2+i] = 0
                            if (dpg.get_value(dpg.get_item_user_data(p["dpg"][i])[1]) == brackets[i]):
                                tmp[2+i] = sys.float_info.epsilon
                        if (tmp[0] == tmp[1] and tmp[2] != 0):
                            if ("range_min" in p and tmp[0] <= p["range_min"]["min"]):
                                tmp[3] = -tmp[3]
                            if ("range_max" in p and tmp[1] >= p["range_max"]["max"]):
                                tmp[2] = -tmp[2]
                        exp_res.params[p["name"]] = tuple(tmp)
                else:
                    exp_res.params[p["name"]] = dpg.get_value(p["dpg"])
        m_algs.run_default_if_params_popup_not_opened()
        work.exp_res[1].params_algs_specials = work.exp_res[0].params_algs_specials
        work.exp_res[1].chosen_algs = work.exp_res[0].chosen_algs

    def save_btn_callback():
        '''
        Button "Сохранить"
        '''
        path = filedialog.asksaveasfilename(filetypes=[("JSON", "*.json")], initialdir=work.working_directory)
        fill_exp_res()
        work.dump_to_file(path)

    def calc_btn_callback(do_new_exp=True):
        '''
        Let's do the experiment
        '''
        fill_exp_res()
        dpg.delete_item(res_group, children_only=True)
        if (do_new_exp):
            for i in range(2):
                cur_exp_mode = exp_modes_keys[last_exp_mode[i]]
                exp_res = work.exp_res[i]
                exp_res.init(len(algs))
                for j in range(work.exp_res[i].exp_count):
                    m = exp_modes_func[last_exp_mode[i]](exp_res.n, **exp_res.params)
                    convert_to_p_matrix(m)
                    do_experiment(m, exp_res)
                exp_res.calculate_average_error(len(algs))
        dpg.push_container_stack(res_group)
        best_alg_max = 0.0
        best_alg = 0
        for i in range(1, len(algs)):
            if (work.exp_res[0].chosen_algs[i] and best_alg_max < work.exp_res[0].phase_averages[i][-1]):
                best_alg = i
                best_alg_max = work.exp_res[0].phase_averages[i][-1]
        if (best_alg != 0):
            dpg.add_text(f"Лучшая стратегия для P - {algs[best_alg]['name']} с сахаристостью {work.exp_res[0].phase_averages[best_alg][-1]} и относительной погрешностью {work.exp_res[0].average_error[best_alg]}")
            dpg.add_text(f"Результат стратегии '{algs[best_alg]['name']}' для P0: сахаристость {work.exp_res[0].phase_averages[best_alg][-1]} и относительная погрешность {work.exp_res[0].average_error[best_alg]}")
        tb, dpg_plot = generate_result_plot_table(work)
        dpg.pop_container_stack()

    def copy_from_p_p0():
        '''
        Copies all parameters from P to P0
        '''
        fill_exp_res()
        cell = dpg.get_item_children(dpg.get_item_children(parameters_table)[1][0])[1][1]
        work.exp_res[1].__dict__ = copy.deepcopy(work.exp_res[0].__dict__)
        dpg.delete_item(cell, children_only=True)
        mode_groups.pop()
        dpg.push_container_stack(cell)
        construct_parameters_table_cell_i(1)
        dpg.pop_container_stack()

    dpg.add_text("Лабораторная работа по сахарной свекле")
    dpg.add_separator()
    work = work_prop()
    work.exp_res = []
    work.exp_res.append(exp_res_props())
    work.exp_res.append(exp_res_props())
    work.working_directory = os.getcwd()
    with dpg.group(horizontal=True):
        dpg.add_text("Рабочая директория")
        working_directory_input = dpg.add_input_text(default_value=work.working_directory, user_data=choose_working_directory_callback, readonly=True)
        dpg.add_button(label="Изменить", user_data=None, callback=lambda sender, app_data, user_data: choose_working_directory_callback(user_data))
    dpg.add_separator()
    dpg.add_button(label="Выбрать из файла", callback=choose_from_file_btn_callback)
    dpg.add_separator()
    exp_count_inputs = [None, None]
    with dpg.group(horizontal=True):
        dpg.add_text("Введите n")
        n_input = dpg.add_input_int(min_value=3, default_value=20, min_clamped=True, callback=set_n)
        set_n(n_input, dpg.get_value(n_input))
    exp_names = ("P (реальный эксперимент)", "P0 (виртуальный эксперимент)")
    mode_groups = []
    parameters_table = dpg.add_table(header_row=False, width=-1, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True)
    for i in range(2):
        work.exp_res[i].exp_mode = last_exp_mode[i]
    construct_parameters_table(parameters_table)
    dpg.add_button(label="Скопировать параметры из P в P0", callback=copy_from_p_p0)
    m_algs = select_algs(work.exp_res[0])
    with dpg.group(horizontal=True):
        dpg.add_button(label="Вычислить", callback=lambda: calc_btn_callback())
        dpg.add_button(label="Сохранить", callback=save_btn_callback)
    dpg.add_text("")
    res_group = dpg.add_group()
