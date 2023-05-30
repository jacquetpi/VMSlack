import time

class SchedulerLocal:
    """
    Main class of the program : watch cpuset usage and VM usage to propose resources
    ...


    """
    def __init__(self, **kwargs):
        req_attributes = ['tick']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        self.delay = 1/self.tick

    def run(self):
        """Run scheduler on specified tick value
        ----------

        """
        while True:
            time_begin = time.time_ns()
            self.__iteration()
            time_to_sleep = (self.delay*10**9) - (time.time_ns() - time_begin)
            if time_to_sleep>0: time.sleep(time_to_sleep/10**9)
        
    def __iteration(self):
        """Execute all actions related to an iteration
        ----------

        """
        # Track cpu usage
        # Track VM usage
        # Mitigate perf?
        # Compute free resources if updated
        print('todo')