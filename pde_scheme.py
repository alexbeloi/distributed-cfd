# numerical pde scheme dependent (e.g. how does solution evolve with time)
import numpde
import operator
import itertools
import local

dt = local.const_dt
dx = local.const_dx
dy = local.const_dx
ax = local.const_ax
ay = local.const_ay

#def Update_Boundary(work):


# rewrite this into Work_Block class in the future -Alex
def Update_Periodic_Boundary(work1, work2):
    # print('in boundary: ', work1.coords, work2.coords)

    # for i in range(work1.dim()):
    #     if work1.coords[i] == work1._stensize and work2.coords[i]== work2._stensize:

    # for cell in work1.loc_left_boundary_cell_list():


    # find workable cells in work1 that need to be given to work2
    span_range = [range(size-2*work1._stensize) for size in work1.size()]

    for j in range(work1.dim()):
        if work1.coords[j] != work2.coords[j]:
            if work1.coords[j] == work1._stensize:
                span_range[j] = range(work1._stensize)
            else:
                span_range[j] = range(work1.size()[j]-3*work1._stensize, work1.size()[j]-2*work1._stensize)

    # print('span should be', span_range)
    # these are the cells in work1 that have links in work2
    swap1 = set(itertools.product(*span_range))

    for cell in swap1:
        # find associated ghost cell in work2
        _temp1 = list(cell)
        _temp2 = list(cell)
        for j in range(work1.dim()):
            if work1.coords[j] != work2.coords[j]:
                if work1.coords[j] == work1._stensize:
                    _temp2[j] = _temp2[j]+work2.size()[j]-2*work2._stensize
                else:
                    _temp2[j] = _temp2[j]-work1.size()[j]+2*work2._stensize

        # print('work1 has size', work1.size())
        # print('trying to get', _temp1, 'from', work1.coords)
        # print('work2 has size', work2.size())
        # print('and put it in', _temp2, 'at', work2.coords)
        work2.set_val_loc(_temp2, float(work1.get_val_loc(_temp1)))

        # print('did it')
        # shift both by stensize in the appropriate components and swap
        for j in range(work1.dim()):
            if span_range[j] == work1._stensize:
                _temp1[j] = _temp1[j] - work1._stensize
                _temp2[j] = _temp2[j] - work2._stensize

        work1.set_val_loc(_temp1, float(work2.get_val_loc(_temp2)))

        #         if cell[i]<work1._stensize and not _is_corner_cell(work1, cell):
        #             _temp = list(cell)
        #             print("fuckin up A in:", work1.coords, "at _temp:", _temp, "and cell", cell)
        #             _temp[i] = work2.size()[i]-2*work2._stensize+_temp[i]
        #             work2.set_val_loc(_temp, float(work1.get_val_loc(cell)))
        #
        # if work2.coords[i] == work2._stensize:
        #     for cell in work2.loc_work_cell_list():
        #         if cell[i]<work2._stensize and not _is_corner_cell(work2, cell):
        #             _temp = list(cell)
        #             print("fuckin up B in:", work2.coords, "at _temp:", _temp, "and cell", cell)
        #             _temp[i] = work1.size()[i]-2*work1._stensize+_temp[i]
        #             work1.set_val_loc(_temp, float(work2.get_val_loc(cell)))

    work1.bdry_ghost_done[work2.coords] = True
    work1.bdry_done[work2.coords] = False

    work2.bdry_ghost_done[work1.coords] = True
    work2.bdry_done[work1.coords] = False

def _is_corner_cell(work, cell):
    for i in range(work.dim()):
        if cell[i] >= work._stensize and cell[i] <= work.size()[i]:
            return False
    return True

# very general way to update block by duplicating array, not the most efficient
# but it is flexible, move into Work_Block class when I find a more general
# way to do stencil computations efficiently
def Update_Block(work):
    temp_array = list(work._array)


    for loc_coords in work.loc_work_cell_list():

        # print('updating cell:', loc_coords)

        numpde.set_val(temp_array, map(operator.add, loc_coords, [work._stensize for i in work.size()]), Update_Cell(work, loc_coords))

        #temp_array[map(operator.add, loc_coords, [work._stensize for i in work.size()])] = Update_Cell(work, loc_coords)

    # print("done updating main cells of: ",work.coords)

    work.array = list(temp_array)

def Update_Flags(work):
    # print("in Update_Flags")
    # print('resetting ghost flags of', work.coords)
    work.reset()

    for key in work.nbr_block_dict:
        work.nbr_block_dict[key].nbr_done[work.coords] = True

        # if neighbor is done too, update each other's shared ghost cells
        # print(work.coords, 'sees neighbor', work.nbr_block_dict[key].coords, 'as done', work.nbr_done[key])

        if work.nbr_done[key]:
            work.update_ghost(work.nbr_block_dict[key])
            work.nbr_block_dict[key].update_ghost(work)
            #numpde.Update_Ghost(work, work.nbr_block_dict[key])
            # print("updating ghost cells in", work.coords, "and", key)

    # update boundary if block is a boundary block
    if work.is_boundary:
        # if periodic
        # print("trying to update periodic boundary")
        for key in work.bdry_block_dict:
            work.bdry_block_dict[key].bdry_done[work.coords] = True
            if work.bdry_done[key]:
                Update_Periodic_Boundary(work, work.bdry_block_dict[key])
        # if not periodic
        # Update_Boundary(work)

    work.time_inc()


# NAIVE APPROACH:
# This function is basically the entire pde scheme and entirely dependent on the
# pde we are trying to solve, we're going to make gross assumptions about
# dimensions and things, what I'm saying is that this is fugly
#
# 1st test with simple multidimensional advection u_t = a*u_x
# u^{t+1}_x = u^t_x + a*dt/dx(u^t_x - u^t_{x-1})
#
# local variable scheme u_xyt, u_111 is the current value of cell being updated
# u_211 denotes the value in cell one "above" in the x component

def Update_Cell(work, cell):
    temp = list(cell)
    u_111 = float(work.get_val_loc(temp))
    temp[0] = temp[0]-1
    u_011 = float(work.get_val_loc(temp))
    temp[0] = temp[0]+1
    temp[1] = temp[1]-1
    u_101 = float(work.get_val_loc(temp))

    return u_111+(ax*dt/dx)*(u_111-u_011) + (ay*dt/dy)*(u_111-u_101)


# LESS NAIVE APPROACH:
# take subarray of stencil size around cell and do linear algebra
#def Update_Cell(work, cell):
