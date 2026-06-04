from threading import Lock


class ApprovalState:

    def __init__(self):

        self.lock=Lock()

        self.pending={}

        self.logs=[]

    def add(self,obj):

        with self.lock:

            self.pending[obj["action_id"]]=obj

    def remove(self,id):

        with self.lock:

            return self.pending.pop(id,None)

    def get_all(self):

        with self.lock:

            return list(self.pending.values())

    def add_log(self,line):

        with self.lock:

            self.logs.append(line)

            self.logs=self.logs[-1000:]

    def get_logs(self):

        with self.lock:

            return self.logs[:]


STATE=ApprovalState()
