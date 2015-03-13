# local criteria for things like setting up initial conditions, boundary, constants

const_rangex = 2*math.pi
const_cfl = 0.9
const_stensize = 5
const_block_size = 128

def Init_Condition(x):
    return math.sin(x)

def Boundary_Initial_Condition(solution, stensize):
    # periodic boundary condition (adding ghost cells)
    solution = solution[-stensize:]+solution
    solution = solution + solution[stensize:2*stensize]
    return solution
