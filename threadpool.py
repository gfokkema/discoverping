from queue import Queue
from threading import Thread


def loop(fn, input, output) -> None:
    while True:
        work = input.get()
        if work:
            output.put(fn(work))
        input.task_done()
        if not work:
            break


class ThreadPool(object):
    def __init__(self, target, num_threads=10):
        self._pending = 0       # definitely not thread-safe
        self._threads = []
        self._input = Queue()   # thread-safe
        self._output = Queue()  # thread-safe

        for i in range(0, num_threads):
            t = Thread(target=loop, args=(target, self._input, self._output))
            t.start()
            self._threads.append(t)

    def __iter__(self):
        return self

    def __next__(self):
        if not self._pending:
            raise StopIteration
        self._pending -= 1
        return self._output.get()

    def join(self):
        for x in range(0, len(self._threads)):
            self._input.put(None)
        self._input.join()
        for t in self._threads:
            t.join()

    def submit(self, work):
        self._pending += 1
        self._input.put(work)
