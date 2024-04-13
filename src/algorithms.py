from src.util import do_rand, clamp
import scipy.optimize
import numpy as np
from typing import Tuple
import math

def hungarian(exp_res, m: np.ndarray, maximize: bool = True) -> Tuple[np.array, float]:
    '''
    Hungarian algorithm (Венгерский алгоритм)
    return (row_ind, col_ind, sum)
    '''
    row_ind: np.array = None
    col_ind: np.array = None
    row_ind, col_ind = scipy.optimize.linear_sum_assignment(m, maximize)
    return (col_ind, m[row_ind, col_ind].sum())

def hungarian_max(exp_res, m: np.ndarray) -> Tuple[np.array, float]:
    '''
    for algs
    Same as hungarian(exp_res, m, True)
    '''
    return hungarian(exp_res, m, True)

def hungarian_min(exp_res, m: np.ndarray) -> Tuple[np.array, float]:
    '''
    for algs
    Same as hungarian(exp_res, m, False)
    '''
    return hungarian(exp_res, m, False)

def greedy_iteration(m: np.ndarray, reserved: np.array, col_ind: np.array, ind_offset: int = 0) -> np.array:
    '''
    Iteration for greedy algorithm
    Is important for lean-greedy and greedy-lean algorithms
    Writes result to col_ind
    reserved - shows, what delivery lot is done (bool array)
    ind_offset is used when we don't start from phase 1, but from phase ind_offset
    '''
    n: int = m.shape[1]
    sz: int = reserved.size
    for i in range(n):
        ind_sorted: np.array = np.flip(np.argsort(m[:, i]))
        j = 0
        while (j < sz and reserved[ind_sorted[j]]):
            j += 1
        col_ind[ind_sorted[j]] = i + ind_offset
        reserved[ind_sorted[j]] = True

def greedy(exp_res, m: np.ndarray) -> Tuple[np.array, float]:
    '''
    Greedy algorithm (Жадный алгоритм)
    return (col_ind, sum)
    '''
    n: int = m.shape[0]
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    greedy_iteration(m, reserved, col_ind)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())

def lean_iteration(m: np.ndarray, reserved: np.array, col_ind: np.array, ind_offset: int = 0, k: int = 1) -> np.array:
    '''
    Iteration for lean algorithm
    Is important for lean-greedy and greedy-lean algorithms
    Writes result to col_ind
    reserved - shows, what delivery lot is done (bool array)
    ind_offset is used when we don't start from phase 1, but from phase ind_offset
    k - used for T(k)G
    '''
    n: int = m.shape[1]
    sz: int = reserved.size
    for i in range(n):
        ind_sorted: np.array = np.argsort(m[:, i])
        j = 0
        min_hit_left = k-1
        while (min_hit_left > 0 or j < sz and reserved[ind_sorted[j]]):
            j += 1
            if (not reserved[ind_sorted[j]]):
                min_hit_left -= 1
        col_ind[ind_sorted[j]] = i + ind_offset
        reserved[ind_sorted[j]] = True

def lean(exp_res, m: np.ndarray) -> Tuple[np.array, float]:
    '''
    Lean algorithm (Бережливый алгоритм)
    return (col_ind, sum)
    '''
    n: int = m.shape[0]
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    lean_iteration(m, reserved, col_ind)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())

def lean_greedy(exp_res, m: np.ndarray, theta: int) -> Tuple[np.array, float]:
    '''
    Lean-greedy algorithm (Бережливо-жадный алгоритм)
    Lean for 1 to theta-1, greedy for theta to n
    return (col_ind, sum)
    '''
    n: int = m.shape[0]
    _theta = clamp(1, theta, n+1)
    if (_theta == 1):
        return lean(exp_res, m)
    if (_theta == n+1):
        return greedy(exp_res, m)
    #if (_theta < 1 or _theta > n+1):
    #    raise Exception("Theta must be from 1 to n+1")
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    lean_iteration(m[:, 0:_theta-1], reserved, col_ind)
    greedy_iteration(m[:, _theta-1:n], reserved, col_ind, _theta-1)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())

def greedy_lean(exp_res, m: np.ndarray, theta: int) -> Tuple[np.array, float]:
    '''
    Greedy-lean algorithm (Жадно-бережливый алгоритм)
    Greedy for 1 to theta, lean for theta+1 to n
    return (col_ind, sum)
    '''
    n: int = m.shape[0]
    _theta = clamp(0, theta, n)
    if (_theta == 0):
        return greedy(exp_res, m)
    if (_theta == n):
        return lean(exp_res, m)
    #if (theta < 0 or theta > n):
    #    raise Exception("Theta must be from 0 to n")
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    greedy_iteration(m[:, 0:_theta], reserved, col_ind)
    lean_iteration(m[:, _theta:n], reserved, col_ind, _theta)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())

def TkG(exp_res, m: np.ndarray, k: int) -> Tuple[np.array, float]:
    '''
    Algorithm T(k)G
    '''
    n = m.shape[0]
    mu = exp_res.get_mu()
    _k = clamp(1, k, n-mu+2)
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    lean_iteration(m[:, 0:mu-1], reserved, col_ind, 0, k)
    greedy_iteration(m[:, mu-1:n], reserved, col_ind, mu-1)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())

def CTG(exp_res, m: np.ndarray) -> Tuple[np.array, float]:
    '''
    Algorithm CTG
    '''
    def gamma(k: int):
        if (1<=k<=mu-1):
            return n-2*mu+2*k+1
        elif (mu<=k<=2*mu-1):
            return n+2*mu-2*k
        else:
            return n-k+1
    n = m.shape[0]
    mu = exp_res.get_mu()
    col_ind: np.array = np.zeros(n, dtype=int)
    sorted_ind: np.array = np.argsort(m[:, 0])
    for i in range(n):
        col_ind[sorted_ind[gamma(i+1)-1]] = i
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())

def Gk(exp_res, m: np.ndarray, k: int) -> Tuple[np.array, float]:
    '''
    Algorithm G^k
    '''
    def Gk_iteration(k: int, reserved: np.array, col_ind: np.array, ind: int) -> None:
        ind_sorted: np.array = np.flip(np.argsort(m[:, ind]))
        for i in range(ind, ind+k):
            j = 0
            while (j < n and reserved[ind_sorted[j]]):
                j += 1
            col_ind[ind_sorted[j]] = i
            reserved[ind_sorted[j]] = True
    n: int = m.shape[0]
    _k = clamp(1, k, n)
    #if (_k > n or _k < 1):
    #    raise Exception("k must be from 1 to n")
    delta_left: int = n % _k
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    for i in range(0, n - delta_left, _k):
        Gk_iteration(_k, reserved, col_ind, i)
    if (delta_left != 0):
        Gk_iteration(delta_left, reserved, col_ind, n - delta_left)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())
