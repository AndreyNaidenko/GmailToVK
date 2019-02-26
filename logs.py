import time


class Logs():
    def __init__(self, max_count=1000):
        self.logs = []
        self.MAX_COUNT = max_count

    def add(self, log):
        if len(self.logs) < self.MAX_COUNT:
            self.logs.append(log)
        else:
            self.clear()

    def get(self, count=2):
        st = ""
        lgs = []
        for i in range(len(self.logs)):
            st = st + self.logs[i] + '\r\n'
            if i % count == 0:
                lgs.append(st)
                st = ""
        return lgs

    def clear(self):
        self.logs = []
