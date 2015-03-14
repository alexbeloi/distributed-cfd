# numerical pde scheme dependent (e.g. how does solution evolve with time)
import numpde
import local

dt = local.const_dt
dx = local.const_dx
dy = local.const_dx
ax = local.const_ax
ay = local.const_ay

#def Update_Boundary(work):


# rewrite this into Work_Block class in the future -Alex
def Update_Periodic_Boundary(work1, work2):
    for i in range(work1.dim()):
        if work1.coords[i] == work1._stensize:
            for cell in work1.loc_work_cell_list():
                if cell[i]<work1._stensize:
                    _temp = cell
                    _temp[i] = work2.size()[i]-work2._stensize+_temp[i]
                    work2.set_val_loc(_temp, float(work1.get_val_loc(cell)))

    if work2.coords[i] == work2._stensize:
        for cell in work2.loc_work_cell_list():
            if cell[i]<work1._stensize:
                _temp = cell
                _temp[i] = work1.size()[i]-work1._stensize+_temp[i]
                work1.set_val_loc(_temp, float(work2.get_val_loc(cell)))

    work1.bdry_ghost_done[work2.coords] = True
    work1.bdry_done[work2.coords] = False

    work2.bdry_ghost_done[work1.coords] = True
    work2.bdry_done[work1.coords] = False

# very general way to update block by duplicating array, not the most efficient
# but it is flexible, move into Work_Block class when I find a more general
# way to do stencil computations efficiently
def Update_Block(work):
    temp_array = list(work.array)

    for loc_coords in work.loc_work_cell_list:
        temp_array[map(operator.add(loc_coords, [work.stensize for i in work.size()]))] = Update_Cell(work, loc_coords)

    work.array = list(temp_array)

def Update_Flags(work):
    for key in work.nbr_block_dict:
        work.nbr_block_dict[key].nbr_done[work.coord] = True
        if work.nbr_done[key]:
            numpde.Update_Ghost(work, work.nbr_block_dict[key])

    # update boundary if block is a boundary block
    if work.is_boundary:
        # if periodic
        for key in work.bdry_block_dict:
            work.bdry_block_dict[key].bdry_done[work.coord] = True
            if work.bdry_done[key]:
                Update_Periodic_Boundary(work, work.bdry_block_dict[key])
        # if not periodic
        # Update_Boundary(work)

    work.reset()
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
    temp = temp[0]+1
    temp[1] = temp[1]-1
    u_101 = float(work.get_val_loc(temp))

    return u_111+(ax*dt/dx)*(u_111-u_011) + (ay*dt/dy)*(u_111-u_101)


# LESS NAIVE APPROACH:
# take subarray of stencil size around cell and do linear algebra
#def Update_Cell(work, cell):
