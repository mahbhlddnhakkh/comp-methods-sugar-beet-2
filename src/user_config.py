from src.algorithms import hungarian_max, hungarian_min, greedy, lean, lean_greedy, greedy_lean, TkG, CTG, Gk
from src.util import generate_matrix_main, generate_matrix_main_ripening, exp_res_props
import math

# Список алгоритмов с названием, указателем на функцию и параметрами (если есть)
# Первый алгоритм всегда должен быть оптимальным максимумом! (относительно первого алгоритма будут считать погрешность)
# "func": def alg(m: np.ndarray, ...) -> Tuple[np.array, float]
algs = [
    {
        "name": "Венгерский алгоритм (максимум)",
        "func": hungarian_max,
    },
    {
        "name": "Венгерский алгоритм (минимум)",
        "func": hungarian_min,
        "check_default": True,
        "hidden": False,
    },
    {
        "name": "Жадный алгоритм",
        "func": greedy,
    },
    {
        "name": "Бережливый алгоритм",
        "func": lean,
    },
    {
        "name": "Бережливо-жадный алгоритм",
        "func": lean_greedy,
        "params": [
            {
                "name": "theta",
                "type": int,
                "default": lambda exp_res: 0 if (exp_res.params == None or not "mu" in exp_res.params) else exp_res.params["mu"],
            },
        ],
    },
    {
        "name": "Жадно-бережливый алгоритм",
        "func": greedy_lean,
        "params": [
            {
                "name": "theta",
                "type": int,
                "default": lambda exp_res: 0 if (exp_res.params == None or not "mu" in exp_res.params) else exp_res.params["mu"],
            },
        ],
    },
    {
        "name": "T(k)G",
        "func": TkG,
        "params": [
            {
                "name": "k",
                "type": int,
                "default": lambda exp_res: 1
            },
        ],
    },
    {
        "name": "CTG",
        "func": CTG,
    },
    {
        "name": "G^k",
        "func": Gk,
        "params": [
            {
                "name": "k",
                "type": int,
                "default": lambda exp_res: 1
            },
        ],
    },
]

# Список указателей на функции режимов
# def generator(n: int, ..., **kwargs) -> np.ndarray:
exp_modes_func = (generate_matrix_main, generate_matrix_main_ripening)

# Список режимов с параметрами
exp_modes = {
    "Без дозаривания": [
        {
            "title": "",
            "name": "Без дозаривания",
            "special": "empty",
        },
        {
            "title": "a_i",
            "name": "a_i",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude", # can be include
                "min": 0
            },
            #"range_max": {
            #    "type": "exclude",
            #    "max": 1
            #}
        },
        {
            "title": "b_ij",
            "name": "b_ij",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude",
                "min": 0
            },
            "range_max": {
                "type": "exclude",
                "max": 1
            }
        },
    ],
    "С дозариванием": [
        {
            "title": "",
            "name": "С дозариванием",
            "special": "empty",
        },
        {
            "title": "a_i",
            "name": "a_i",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude",
                "min": 0
            },
            #"range_max": {
            #    "type": "exclude",
            #    "max": 1
            #}
        },
        {
            "title": "b_ij во время дозаривания",
            "name": "b_ij_1",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude",
                "min": 1
            },
        },
        {
            "title": "b_ij после дозаривания",
            "name": "b_ij_2",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude",
                "min": 0
            },
            "range_max": {
                "type": "exclude",
                "max": 1
            }
        },
        {
            "title": "mu",
            "name": "mu",
            "type": int,
        }
    ],
}
