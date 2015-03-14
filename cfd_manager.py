import threading
import time
import xmlrpclib
import sys
import numpde
import pde_scheme
import local
import itertools
from SimpleXMLRPCServer import SimpleXMLRPCServer

#
# Work Queue
#
# add:      register a new work item
# work:     return oldest incomplete work item
# complete: mark work item as complete
# stats:    return work statistics
#
# we use coords and time_step to record finished blocks and
# store the actual block data in a dictionary for later reference

class WorkQueue(object):
    def __init__(self):
        self._incomplete = []
        self._completed = set()

    def add(self, work):
        self._incomplete.append(work)

    def add_finished_with_neighbors(self, work):
        self._completed_with_neighbors.append(work)

    def work(self):
        while self._incomplete:
            work = self._incomplete.pop()
            if work not in self._completed:
                self.add(work)
                return work
        return None

    def complete(self, work):
        _stamp = (work.coords, work.time_step)
        dupe = _coords in self._completed
        if not dupe:
            self._completed.add(_stamp)
            self._block_dict[_coords] = work
        return dupe

    def check_completed(self, work):
        return work.coords in self._completed

class WorkGenerator(object):
    def __init__(self, solution):
        self._solution = solution
        self._done = False
        self._work = self.__work_generator()

    def __work_generator(self):
        for x in self._solution.blocks:
            yield x
        self._done = True

    def __iter__(self):
        return self._work

    def next(self):
        return next(self._work)

class Problem(object):
    def __init__(self, solution, output, finish_time):
        self._output = output
        self._solution = solution
        # self.block_holder = numpde.Empty_Solution_Block_Holder(self._solution,block_size)

        if self._output:
            with open(self._output, 'w') as f:
                f.write("N=%d \n" % len(self._solution))
                f.flush()

        self._work_queue = WorkQueue()
        self._work_maker = WorkGenerator(self._solution)

        self._lock = threading.Lock()

        # self._mon_thread = threading.Thread(target=self.__monitor)
        # self._mon_thread.daemon = True
        # self._mon_thread.start()

    def __get_work(self):
        try:
            # fill up the work queue with new work
            work = next(self._work_maker)
            self._work_queue.add(work)
            return work
        except StopIteration:
            pass
        # now drain the work queue
        return self._work_queue.work()

    def __report_unlocked(self):
        print self._work_maker.progress()

    # def __monitor(self):
    #     while True:
    #         with self._lock:
    #             self.__report_unlocked()
    #         time.sleep(1)

    def get_work(self):
        with self._lock:
            part = self.__get_work()
            if not part:
                return None
            return part

    def finish_work(self, work):
        with self._lock:
            dupe = self._work_queue.complete(work)
            if dupe:
                return

            # record finished work
            pde_scheme.Update_Flags(work)

            if self._output:
                with open(self._output, 'a') as f:
                    for cell in work.work_cell_list():
                        f.write(work.real_cell_out(cell))
                    f.flush()

            # if we haven't reached finish time, there's more work to do
            if work.time_step*local.const_dt < finish_time:
                # check if this block finished all its ghost cell updates, if
                # so add it back to the queue
                if all(work.nbr_ghost_done.values()) and all(work.bdry_ghost_done.values()):
                    self._work_queue.add(work)
                # check if its ok to add the neighbors to the queue too
                for neighor in work.nbr_block_dict.values():
                    if all(neighbor.nbr_ghost_done.values()):
                        self._work_queue.add(neighbor)

class ProblemProxy(object):
    def __init__(self, problem):
        self._prob = problem

    def get_work(self):
        return self._prob.get_work()

    def finish_work(self, work):
        self._prob.finish_work(spec, results)


if __name__ == '__main__':

    finish_time = int(sys.argv[1])

    rangex = local.const_range
    cfl = local.const_cfl
    stensize = local.const_stensize
    block_size = local.const_block_size

    output = None
    if len(sys.argv) == 3:
        output = sys.argv[2]

    # Get initial condition and boundary conditions from local.py
    solution = numpde.Solution(local.Init_Condition(), block_size, stensize, True)

    print "starting problem", num_cells, cfl

    p = Problem(solution, output, finish_time)
    pp = ProblemProxy(p)

    server = SimpleXMLRPCServer(("0.0.0.0", 8000), logRequests=False,
            allow_none=True)
    server.register_instance(pp)
    server.serve_forever()
