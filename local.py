# local criteria for things like setting up initial conditions, boundary, constants
import numpde
import math
import itertools

const_range = 2*math.pi
const_cfl = 0.9
const_stensize = 1
const_dim = 2
const_num_cells = 16
const_block_size = 8

const_ax = -0.7
const_ay = -0.2
const_dx = const_range/const_num_cells
const_dt = const_cfl*const_dx/(abs(const_ax)+abs(const_ay))

def init_condition():
    _array = [ list([list([]) for i in range(const_num_cells)]) for i in range(const_num_cells)]

    _temp = itertools.product(*[range(const_num_cells) for i in range(const_dim)])

    for index in _temp:
        numpde.set_val(_array, index, math.sin((index[0]+index[1]+1)*const_range/float(const_num_cells)))
    return _array

def add_ghost_cells(array, stensize, periodic=False):
    if periodic:
        if type(array[0]) is list:
            for i in range(len(array)):
                 array[i] = add_ghost_cells(array[i],stensize, periodic)
        _temp = list(array)
        _temp = array[-stensize:]+_temp
        _temp = _temp + array[0:stensize]
        return _temp
    else:
        pass# some other boundary condition
