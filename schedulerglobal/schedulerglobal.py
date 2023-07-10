import time
from schedulerglobal.apirequest.apirequester import ApiRequester
from schedulerglobal.apiendpoint.apiendpoint import ApiEndpoint

class SchedulerGlobal(object):
    """
    The Global scheduler is in charge of selecting the most appropriate host for new deployments
    ...

    Attributes
    ----------
    url_list : list
        List of node urls
    known_vm : dict
        VM name associated to their current host

    Public Methods
    -------
    run()
        Run the global scheduler
    """
    def __init__(self, **kwargs):
        req_attributes = ['api_url', 'api_port', 'url_list', 'delay']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        
        self.endpoint = ApiEndpoint(api_url=self.api_url, api_port=self.api_port, scheduler_global=self)
        self.endpoint.run()
        self.requester = ApiRequester()
        self.known_vm = dict()

    def run(self):
        """Run scheduler with specified delay
        ----------
        """
        launch_at = time.time_ns()
        while True:
            time_begin = time.time_ns()

            self.__iteration(time_since_launch=int((time_begin-launch_at)/(10**9)))
            
            time_to_sleep = (self.delay*10**9) - (time.time_ns() - time_begin)
            if time_to_sleep>0: time.sleep(time_to_sleep/10**9)
            else: print('Warning: overlap iteration', -(time_to_sleep/10**9), 's')

    def __iteration(self, time_since_launch : int):
        """Execute all actions related to an iteration
        ----------

        """
        pass  # Update monitoring?
        
    def deploy(self, name : str, cpu : str, memory : str, ratio : str, disk : str):
        """Deploy a VM to the cluster
        ----------

        Parameters
        ----------
        name : str
            VM name as str
        cpu : str
            Number of vcpu as str
        memory : str
            Memory (gb) as str
        ratio :  str
            Premium policy to apply
        disk :  str
            Disk location

        Returns
        -------
        response : str
            Return result of operation as str
        """
        # Select the most appropriate cluster
        # Deploy 
        # Update list of known VM
        return 'TODO'

    def remove(self, name : str):
        """Remove a VM from the cluster
        ----------

        Parameters
        ----------
        vm : str
            Name of VM to be removed

        Returns
        -------
        response : str
            Return result of operation as str
        """
        if name not in self.known_vm:
            return 'Unknown VM'
        return self.requester.remove(host_url=self.known_vm[name], name=name)

    def status(self):
        """Return the current cluster state
        ----------

        Returns
        -------
        state : str
            Cluster related info as str
        """
        global_status = dict()
        for node_url in self.url_list:
            try:
                global_status[node_url] = self.requester.status_of(host_url=node_url)
            except Exception as e:
                print('Info: Error with url', node_url, str(e))
        return global_status