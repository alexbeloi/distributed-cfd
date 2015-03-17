import sys
import argparse
import xmlrpc.client
import time
import threading
import numpde
import pde_scheme
import time

# xmlrpclib.Marshaller.dispatch[type(0L)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)
# xmlrpclib.Marshaller.dispatch[type(0)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)

def setup_block(work_spec):
    coords = work_spec.get('coords', None)
    array = work_spec.get('array', None)
    stensize = work_spec.get('stensize', None)
    time_step = work_spec.get('time_step', None)
    work = numpde.Work_Block(coords, array, stensize, time_step)
    return work

class Worker(threading.Thread):
    def __init__(self, host, port):
        super(Worker, self).__init__()
        address = "http://%s:%s" % (host, port)
        self._server = xmlrpc.client.ServerProxy(address)
        self.daemon = True

    def run(self):
        while True:
            work_spec = self._server.get_work()
            if not work_spec:
                print("no work available... waiting")
                time.sleep(10)
                continue
            work = setup_block(work_spec)

            _start_time = time.time()
            pde_scheme.Update_Block(work)
            _end_time = time.time()
            # print('finished work on:', work.coords, 'time: ', work.time_step, 'work took: ', _end_time-_start_time, 'ms')
            self._server.finish_work({'coords':tuple(work.coords), 'array':work._array})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("num_workers", type=int, default=1)
    parser.add_argument("host", type=str, default="localhost")
    parser.add_argument("port", type=str, default="8000")
    args = parser.parse_args()

    # start the workers
    workers = []
    for _ in range(args.num_workers):
        worker = Worker(args.host, args.port)
        worker.start()
        workers.append(worker)
    for worker in workers:
        worker.join()
