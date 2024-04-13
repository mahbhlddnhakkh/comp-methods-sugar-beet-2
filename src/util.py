from src.config import CFG
from typing import Tuple, Dict, List
import numpy as np
import os.path
import json
import math
import sys

class exp_res_props:
    '''
    Represents props of advanced experiment
    '''
    n: int = 3
    exp_count: int = 1
    # P or P0
    exp_name: str = None
    # Ripening or without ripening
    exp_mode: int = None
    # index of chosen algs. Should be sorted, size must be <= len(algs), each element must be from 0 to len(algs)
    chosen_algs: List[int] = None
    # contain basic information. string: string
    params: dict = None
    # contain arguments for some algorithms. E.g. theta for lean greedy and greedy lean. alg_ind: [param1, param2, ...] . already checked
    params_algs_specials: List[list] = None
    # stores average S (for every experiment) for each algorithm on each phase ; alg_ind: [s_avg_phase_1, ..., s_avg_phase_n]
    phase_averages: List[List[float]] = None
    # stores results for each algorithm on the last experiment (useful in manual)
    #last_res: List[tuple] = None
    # stores average differences for each algorithm
    average_error: List[float] = None
    #mu: int = 0

    def init(self, algs_len):
        '''
        Call before doing experiment
        '''
        #self.params = {}
        self.phase_averages = [[0.0]*self.n for i in range(algs_len)]
        self.last_res = [None]*algs_len

    def calculate_average_error(self, algs_len):
        '''
        Call after doing experiment
        '''
        self.average_error = [None]*algs_len
        for i in range(algs_len):
            self.average_error[i] = (self.phase_averages[0][-1] - self.phase_averages[i][-1]) / self.phase_averages[0][-1]

    def dump_to_file(self, path: str) -> None:
        '''
        Dumps properties to json file
        '''
        if (path == "" or path == ()):
            return
        # since we are dumping this, we probably don't need last result anymore (we shouldn't dump in manual tab)
        #self.last_res = None
        #self.path = None
        #self.working_directory = None
        with open(path, "w", encoding="utf-8-sig") as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)
        #self.path = path
        #self.working_directory = os.path.dirname(path)

    def get_from_file(self, path: str) -> None:
        '''
        Gets properties from json file
        '''
        if (path == "" or path == ()):
            return
        tmp = None
        with open(path, "r", encoding="utf-8-sig") as f:
            tmp = json.load(f)
        self.__dict__ = tmp
        #self.path = os.path.abspath(path)
        #self.working_directory = os.path.dirname(self.path)
        self.fix_algs_params_keys()

    def fix_algs_params_keys(self) -> None:
        '''
        For whatever reason json doesn't allow int to be keys for dict so they are strings now. Needs to be fixed.
        '''
        before_keys = tuple(self.params_algs_specials.keys())
        for key in before_keys:
            if (type(key) is str):
                self.params_algs_specials[int(key)] = self.params_algs_specials.pop(key)

    def __str__(self):
        #return json.dumps(dict(self.__dict__, **{"last_res": None}), ensure_ascii=False)
        return str(self.__dict__)
    
    def __repr__(self):
        return f'exp_res_props({self.__dict__})'

    def get_mu(self) -> int:
        return 0 if (self.params == None or not "mu" in self.params) else self.params["mu"]

class work_prop:
    '''
    Contains all (2) exp_res_props and working group. 
    '''
    # stores path to dir which contains json
    path: str = None
    # stores current working directory
    working_directory: str = None
    exp_res: list[exp_res_props] = []
    variance = None

    def dump_to_file(self, path: str) -> None:
        '''
        Dumps properties to json file
        '''
        if (path == "" or path == ()):
            return
        self.path = None
        self.working_directory = None
        tmp = self.__dict__.copy()
        tmp["exp_res"] = []
        for i in range(len(self.exp_res)):
            tmp["exp_res"].append(self.exp_res[i].__dict__)
        with open(path, "w", encoding="utf-8-sig") as f:
            json.dump(tmp, f, indent=2, ensure_ascii=False)
        self.path = path
        self.working_directory = os.path.dirname(path)

    def get_from_file(self, path: str) -> None:
        '''
        Dumps properties to json file
        '''
        if (path == "" or path == ()):
            return
        tmp: dict = None
        with open(path, "r", encoding="utf-8-sig") as f:
            tmp = json.load(f)
        exp_res = tmp["exp_res"].copy()
        tmp["exp_res"] = self.exp_res
        for i in range(len(self.exp_res)):
            tmp["exp_res"][i] = self.exp_res[i]
            tmp["exp_res"][i].__dict__ = exp_res[i]
        self.__dict__ = tmp
        self.path = os.path.abspath(path)
        self.working_directory = os.path.dirname(self.path)
        for exp in self.exp_res:
            exp.fix_algs_params_keys()
    
    def __str__(self):
        return str(self.__dict__)
    
    def __repr__(self):
        return f'work_prop({self.__dict__})'

def do_rand(shape: tuple, v_min, v_max) -> np.ndarray:
    '''
    Return random ndarray with values from v_min to v_max
    shape is a size tuple. E.g. shape=(2, 3) is matrix with sizes (2, 3)
    '''
    return (np.random.rand(*shape) * (v_max - v_min) + v_min)

def convert_to_p_matrix(m: np.ndarray) -> None:
    '''
    Converts vector 'a' and matrix B, where 'a' in the first row of the matrix 'm' and the rest of the 'm' is B
    Elements of B must be between 0 and 1 (exceeding 1 is possible though)
    It modifies 'm'
    '''
    n: int = m.shape[0]
    for i in range(1, n):
        m[:, i] = m[:, i] * m[:, i-1]

def convert_special_range_to_range(x: tuple) -> tuple:
    '''
    Converts (v_min, v_max, v_min_epsilon, v_max_epsilon) to (v_min_calc, v_max_calc)
    '''
    return (x[0] + x[2], x[1] - x[3])

def generate_matrix_main_ripening(n: int, a_i: Tuple[float, float], b_ij_1: Tuple[float, float], b_ij_2: Tuple[float, float], mu: int, **kwargs) -> np.ndarray:
    '''
    Generates matrix with ripening
    Uses parameters a_i, b_i_j_1, b_i_j_2 <- tuples with min and max values for each
    '''
    _mu = clamp(0, mu, n-1)
    m: np.ndarray = np.zeros((n, n), dtype=float)
    m[:, 0] = do_rand((n, ), *convert_special_range_to_range(a_i))
    m[:, 1:_mu+1] = do_rand((n, _mu), *convert_special_range_to_range(b_ij_1))
    m[:, _mu+1:n] = do_rand((n, n-1-_mu), *convert_special_range_to_range(b_ij_2))
    return m

def generate_matrix_main(n: int, a_i: Tuple[float, float], b_ij: Tuple[float, float], **kwargs) -> np.ndarray:
    '''
    Generates matrix without ripening
    Uses parameters a_i, b_i_j <- tuples with min and max values for each
    '''
    m: np.ndarray = np.zeros((n, n), dtype=float)
    m[:, 0] = do_rand((n, ), *convert_special_range_to_range(a_i))
    m[:, 1:n] = do_rand((n, n-1), *convert_special_range_to_range(b_ij))
    return m

def clamp(min_val, val, max_val):
    if (val < min_val): return min_val
    if (val > max_val): return max_val
    return val