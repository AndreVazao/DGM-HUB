from dgm_hub.runtime.event_bus import EventBus

class PlanDispatcher:
    def __init__(self, bus: EventBus):
        self.bus = bus

    def dispatch(self, plan):
        self.bus.emit("plan_created", plan)
