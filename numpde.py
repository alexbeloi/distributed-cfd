import math
import operator
import itertools

# Work Block
#
# array:    data storage
# start:    global coords of "top-left" corner of workable block
# end:      global coords of "bottom-right" corner of workable block
# dim:      returns dimension of array (e.g. a 3x3 matrix will have dim=2)
# size:     returns the actual size of each dimension (e.g. a 3x3 matrix will have size=[3,3])
#

class Work_Block(object):
    def __init__(self, coords, array, stensize, time_step=0):
        self.coords = coords
        self._start = coords
        self._array = array
        self._stensize = stensize
        self._end = self.__end()
        self._dimension = dimension(array)
        self.time_step = time_step

        # neighbor data
        self.nbr_block_dict = {}
        self.nbr_done = {}
        self.nbr_ghost_done = {}

        # boundary flags
        self.bdry_block_dict ={}
        self.bdry_done = {}
        self.bdry_ghost_done = {}

    def add_neighbor(self, work2):
        self.nbr_block_dict[work2.coords] = work2
        self.nbr_done[work2.coords] = False
        self.nbr_ghost_done[work2.coords] = False

    def add_bdry(self, work2):
        self.bdry_block_dict[work2.coords] = work2
        self.bdry_done[work2.coords] = False
        self.bdry_ghost_done[work2.coords] = False

    def __end(self):
        _temp = map(operator.add, self.coords, self.size())
        __temp = map(operator.sub, _temp, [2*self._stensize for i in range(self.dim())] )
        return __temp

    def dim(self):
        return dimension(self._array)

    def size(self):
        return array_size(self._array)

    def get_val_glob(self, position):
        return self.get_val_loc(self._glob_to_loc(position))

    def set_val_glob(self, position, value):
        self.set_val_loc(self._array, self._glob_to_loc(position), value)

    def get_val_loc(self, position):
        return get_val(self._array, map(operator.add(position, [self._stensize for i in range(self.dim())])))

    def set_val_loc(self, position, value):
        set_val(self._array, map(operator.add(position, [self._stensize for i in self.size()])), value)

    def _glob_to_loc(self, glob_coords):
        return map(operator.sub(glob_coords, self._start))

    def time_inc(self):
        self.time_step = self.time_step+1

    def cell_list(self):
        _temp_start = [x-self._stensize for x in self._start]
        _temp_end = [x+self._stensize for x in self._end]
        return list(itertools.product(*[range(_temp_start[i],_temp_end[i]) for i in range(self.dim()) ] ) )

    def work_cell_list(self):
        return list(itertools.product(*[range(self._start[i],self._end[i]) for i in range(self.dim()) ] ) )

    def loc_work_cell_list(self):
        return list(itertools.product(*[range(0,self._end[i]-self._stensize) for i in range(self.dim()) ] ) )

    def reset(self):
        for key in self.nbr_ghost_done:
            self.nbr_done[key] = False

    def is_boundary(self):
        for i in range(self.dim()):
            if self.work.coords[i] == self.stensize or self.coords[i] + self._block_size > self.size()[i]:
                return True
        return False

    # gives nice printable output, given an element of work_cell_list
    def real_cell_out(self, cell):
        _temp = tuple(map(operator.sub(map(operator.add(cell, self._start)),[self._stensize for i in range(self.dim())])))
        _temp.append(self.time_step)
        _temp.append(self.get_val_loc(cell))
        return _temp

# Solution
#
# Block_Generator:  partitions initial_state into Work_Block pieces
# fill_neighbors:   gives pointers to blocks so they know their neighbors

class Solution(object):
    def __init__(self, initial_state, block_size, stensize, periodic=False, time_step=0):
        self._array = initial_state
        self._block_size = block_size
        self._stensize = stensize
        self._dimension = dimension(self._array)
        self.periodic = periodic
        self._size = array_size(self._array)
        self.blocks = list(self.Block_Generator())
        self._block_dict = {}
        self.fill_neighbors()

    def dim(self):
        return self._dimension

    def size(self):
        return self._size

    def Block_Generator(self):
        for coords in itertools.product(*[xrange(self._stensize,comp_dim-self._stensize,self._block_size) for comp_dim in self.size()]):
            start = [x-self._stensize for x in coords]
            end = [min(coords[i]+self._block_size+self._stensize,self.size()[i]) for i in range(len(coords))]

            # print 'coords in block_gen: {}'.format(coords)
            # print 'start and end in block_gen: {} {}'.format(start, end)

            yield Work_Block(coords, get_subarray(self._array, start, end), self._stensize)

    def fill_neighbors(self):
        for block in self.blocks:
            self._block_dict[block.coords] = block
        for block in self.blocks:
            for neighbor in self.neighbors(block):
                block.add_neighbor(neighbor)

            # if boundary is periodic, must also keep track of blocks on opposite
            # end of the solution space
            if self.periodic:
                if block.is_boundary:
                    for i in range(block.dim()):
                        _temp = list(block.coords)
                        if block.coords[i] == self._stensize:
                            _temp[i] = xrange(self._stensize, self.size()[i] - self._stensize, self._block_size)[-1]
                            block.add_bdry(self._block_dict[tuple(_temp)])
                        elif block.coords[i] == xrange(self._stensize, self.size()[i] - self._stensize, self._block_size)[-1]:
                            _temp[i] = self._stensize
                            block.add_bdry(self._block_dict[tuple(_temp)])


    def add_block(self, work):
        self._block_dict[work.coords] = work
        self.blocks.append(work)

    def get_block(self, coords):
        if coords in self._block_dict:
            return self._block_dict[coords]
        return False

    def neighbors(self, work):
        return [self._block_dict[neighbor] for neighbor in self.neighbor_coords(work)]

    def neighbor_coords(self, work):
        _temp = work.coords
        _temp_list = [map(operator.add, _temp, item) for item in self._shifts(self._block_size, self.dim())] + [map(operator.sub, _temp, item) for item in self._shifts(self._block_size, self.dim())]
        return [tuple(neighbor) for neighbor in _temp_list if self._valid_coord(neighbor) and neighbor != _temp]

    # boring stuff for detecting/finding neighbor cells
    def _valid_coord(self, coords):
        for i in range(self.dim()):
            if coords[i] <0 or coords[i] >= self.size()[i]:
                return False
        return True



    # simple function to generate all tuples of a certain length with
    # letters '0' and 'block_size'
    # http://stackoverflow.com/questions/19671826/possible-binary-numbers-function-python
    def _shifts(self, block_size, N):
        import itertools
        return itertools.product((0, block_size), repeat=N)

    def time_inc(self):
        self.time_step = self.time_step+1

# update the ghost cells between work blocks 'work1' and 'work2'
#
# should be "simple" to calculate which blocks overlap based on coordinates of
# the given blocks instead of doing a list intersection (which is probably
# expensive
#
# rewrite this into the Work_Block class in the future -Alex
def Update_Ghost(work1, work2):
    _temp = set(work2.work_cell_list())
    for cell in work1.cell_list():
        if cell in _temp:
            work1.set_val_glob(cell, float(work2.get_val_glob(cell)))

    _temp = set(work1.work_cell_list())
    for cell in work2.cell_list():
        if cell in _temp:
            work2.set_val_glob(cell, float(work1.get_val_glob(cell)))

    work1.nbr_ghost_done[work2.coords] = True
    work1.nbr_done[work2.coords] = False

    work2.nbr_ghost_done[work1.coords] = True
    work2.nbr_done[work1.coords] = False

def Update_Ghost_All(work):
    for key,block in work.nbr_block_dict:
        Update_Ghost(work,block)
        work.nbr.done[key] = False



# GENERAL ARRAY FUNCTIONS

# compute dimension of array (e.g. [[1,2,3],[0,1,4]] has dimension 2)
def dimension(array):
    return len(array_size(array))

def array_size(array, dimensions=[]):
    _temp = list(dimensions)
    if type(array[0]) is list:
        _temp.append(len(array))
        return array_size(array[0], _temp)
    _temp.append(len(array))
    return _temp

# gets subarray from array, the components of tuples index_start and index_end
# define range to pick in each dimension
#
# probably very slow, replace with numpy implementation later
def get_subarray(array, index_start, index_end):
    subarray = array[index_start[0]:index_end[0]+1]
    if type(subarray[0]) is not list:
        return subarray
    subarray = [get_subarray(component,index_start[1:],index_end[1:]) for component in subarray]
    return subarray

# returns pointer to lowest dimension "row" in array at index "index",
# e.g. if index = (x,y,z), returns reference to array[x][y]
def deepest_array(array, index):
    sub_array = array[index[0]]
    for component in index[1:-1]:
        sub_array = sub_array[component]
    return sub_array

# gets value of array at coordinates given by index
# e.g. if index = (x,y,z), returns array[x][y][z]
def get_val(array, index):
    return deepest_array(array, index)[index[-1]]

# sets the value of component of array at tuple "index" to "value"
def set_val(array, index, value):
    deepest_array(array, index)[index[-1]] = value
