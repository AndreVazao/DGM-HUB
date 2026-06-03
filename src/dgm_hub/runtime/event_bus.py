from collections import defaultdict

class EventBus:
    def __init__(self):
        self.listeners = defaultdict(list)

    def subscribe(self, event: str, callback):
        self.listeners[event].append(callback)

    def emit(self, event: str, data=None):
        for cb in self.listeners[event]:
            cb(data)
