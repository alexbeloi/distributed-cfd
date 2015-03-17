import math
import threading
import time
import xmlrpc.client
import sys
import numpde
import pde_scheme
import local
import itertools
import json
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

#
# Work Queue
#
# add:      register a new work item
# work:     return oldest incomplete work item
# complete: mark work item as complete
#
# we use coords and time_step to record finished blocks

class WorkQueue(object):
    def __init__(self):
        self._incomplete = []
        self._completed = set()

    def add(self, work):
        self._incomplete.insert(0, work)

    def work(self):
        qu = [stuff.coords for stuff in self._incomplete]
        print('trying to get work, here is the current queue: ', qu)

        while self._incomplete:
            work = self._incomplete.pop()
            if not self.check_completed(work):
                self._completed.add(work)

                return work
        return None

    def complete(self, work):
        _stamp = (work.coords, work.time_step)
        dupe = _stamp in self._completed
        if not dupe:
            self._completed.add(_stamp)
        return dupe

    def check_completed(self, work):
        return (work.coords, work.time_step) in self._completed

# class WorkGenerator(object):
#     def __init__(self, solution):
#         self._solution = solution
#         self._done = False
#         self._work = self.__work_generator()
#
#     def __work_generator(self):
#         for x in self._solution.blocks:
#             yield x
#         self._done = True
#
#     def __iter__(self):
#         return self._work
#
#     def next(self):
#         return next(self._work)

class Problem(object):
    def __init__(self, solution, output, finish_time):
        self._output = output
        self._solution = solution

        self._finished_cells = [list([]) for _ in range(100)] #figure out a better way
        self._expected_cells = int(math.pow(local.const_num_cells,self._solution.dim()))

        self._current_time_step = 1

        if self._output:
            with open(self._output, 'w') as f:
                f.write("N=%d \n" % self._solution.size()[0])
                f.flush()

        self._work_queue = WorkQueue()
        self._queue_init_fill()

        # self._work_maker = WorkGenerator(self._solution)

        self._lock = threading.Lock()

    def _queue_init_fill(self):
        for block in self._solution.blocks:
            self._work_queue.add(block)
            print(block.coords)

    # def __get_work(self):
    #     print('inside of __get_work')
    #     try:
    #         # fill up the work queue with new work
    #         _temp = iter(self._work_maker)
    #         work = next(_temp)
    #         self._work_queue.add(work)
    #         return work
    #     except StopIteration:
    #         pass
    #     # now drain the work queue
    #     return self._work_queue.work()

    def get_work(self):
        print('test1')
        with self._lock:
            work = self._work_queue.work()
            if not work:
                return None
            return {'coords':work.coords, 'array':work._array, 'stensize':work._stensize, 'time_step':work.time_step}

    def _rebuild(self, output_spec):
        coords = output_spec['coords']
        array = output_spec['array']

        work = self._solution._block_dict[tuple(coords)]
        work._array = array

        return work

    def _arrange_output(self, work):
        for item in work.loc_work_cell_list():
            cell = work.real_cell_out(item)
            self._finished_cells[work.time_step].append(cell)

        while len(self._finished_cells[self._current_time_step]) == self._expected_cells:
            if self._output:
                with open(self._output, 'a') as f:
                    for cell in self._finished_cells[self._current_time_step]:
                        json.dump(cell, f)
                        f.write('\n')
                    f.flush()


            print("finished time: ", local.const_dt*self._current_time_step,)
            self._current_time_step = self._current_time_step+1

    def finish_work(self, output_spec):
        with self._lock:
            work = self._rebuild(output_spec)
            dupe = self._work_queue.complete(work)
            if dupe:
                return

            # qu = [stuff.coords for stuff in self._work_queue._incomplete]
            # print(work.coords, 'just finished and here is the current queue: ', qu)

            # record finished work
            pde_scheme.Update_Flags(work)

            # print("finished flags for: ", work.coords)
            self._arrange_output(work)



            # if we haven't reached finish time, there's more work to do
            if work.time_step*local.const_dt < finish_time:
                # check if this block finished all its ghost cell updates, if
                # so add it back to the queue
                # print('checking nbr_done flags of ', work.coords)
                # for flag in work.nbr_done.values():
                #     print(flag)
                #
                # print('checking bdry_ghost_done flags of ', work.coords)
                # for flag in work.bdry_ghost_done.values():
                #     print(flag)
                if all(work.nbr_ghost_done.values()) and all(work.bdry_ghost_done.values()):
                    self._work_queue.add(work)
                # check if its ok to add the neighbors to the queue too
                for neighbor in work.nbr_block_dict.values():
                    if all(neighbor.nbr_ghost_done.values()):
                        self._work_queue.add(neighbor)

# http://stackoverflow.com/questions/4659579/how-to-see-traceback-on-xmlrpc-server-not-client
class Handler(SimpleXMLRPCRequestHandler):
     def _dispatch(self, method, params):
         try:
             return self.server.funcs[method](*params)
         except:
             import traceback
             traceback.print_exc()
             raise

class ProblemProxy(object):
    def __init__(self, problem):
        self._prob = problem
    def get_work(self):
        return self._prob.get_work()

    def finish_work(self, output_spec):
        self._prob.finish_work(output_spec)


if __name__ == '__main__':

    finish_time = int(sys.argv[1])

    num_cells = local.const_num_cells
    rangex = local.const_range
    cfl = local.const_cfl
    stensize = local.const_stensize
    block_size = local.const_block_size

    output = None
    if len(sys.argv) == 3:
        output = sys.argv[2]

    # Get initial condition and boundary conditions from local.py
    ic = local.init_condition()
    ic = local.add_ghost_cells(ic, stensize, True)
    solution = numpde.Solution(ic, block_size, stensize, True)

    print("starting problem", num_cells, cfl)

    p = Problem(solution, output, finish_time)
    pp = ProblemProxy(p)

    # test = pp.get_work()

    # server = SimpleXMLRPCServer(("0.0.0.0", 8000), logRequests=False,            allow_none=True)
    server = SimpleXMLRPCServer(("0.0.0.0", 8000), Handler)
    server.register_instance(pp)
    server.serve_forever()
