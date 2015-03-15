# local criteria for things like setting up initial conditions, boundary, constants
import numpde
import math
import itertools

const_range = 2*math.pi
const_cfl = 0.9
const_stensize = 2
const_dim = 2
const_num_cells = 1024
const_block_size = 128

const_ax = -0.7
const_ay = -0.2
const_dx = const_range/const_num_cells
const_dt = const_cfl

def Init_Condition():
    _array = [[(i+0.5)*const_range/float(const_num_cells)] for i in range(const_num_cells)]
    _temp = list(_array)
    _array = [[ item + cell for item in _temp]  for cell in _array]

    _temp = itertools.product(*[range(const_num_cells) for i in range(const_dim)])

    for index in _temp:
        numpde.set_val(_array, index, math.sin((index[0]+0.5)*const_range/float(const_num_cells)))
    return _array

def Add_Ghost_Cells(array, stensize, periodic=False):
    if periodic:
        # periodic boundary condition (adding ghost cells)
        if type(array[0]) is list:
            for row in array:
                Add_Ghost_Cells(array[row],stensize, periodic)
        array = array[-stensize:]+array
        array = array + array[stensize:2*stensize]
    else:
        pass# some other boundary condition
