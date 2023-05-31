from schedulerlocal.node.servercpuset import ServerCpuSet
from schedulerlocal.domain.libvirtconnector import LibvirtConnector

class AllocationTracker(object): # Abstract class
    """
    A tracker is a class in charge of monitoring the resources allocated and compute available ones
    ...

    Attributes
    ----------
    generic_tracking : dict
        Dict with physical cpuid as key associated to the list of pinned VM
    specific_tracking : dict
        Dict with physical cpuid as key associated to a [0;1] value representing the free part on the cpu (while logic being implemented in child class)

    Public Methods
    -------
    build_specific_tracker_dict()
        Return a dict of free portion on each cpuid. Must be reimplemented
    update_tracker()
        Update tracking dicts. Must be reimplemented
    available_resources()
        Return available resources. Must be reimplemented
    """

    def __init__(self, **kwargs):
        req_attributes = ['cpuset', 'connector']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        self.generic_tracking = self.__build_generic_tracker_dict()
        self.specific_tracking = self.build_specific_tracker_dict()
        
    def __build_generic_tracker_dict(self):
        """Return a dict of allocated VMs to each cpuid
        ----------
        """
        tracking = dict()
        for cpu in self.cpuset.get_cpu_list(): tracking[cpu.get_cpu_id()] = list()
        for vm in self.connector.get_vm_alive_as_entity():
            for cpuid, is_pinned in vm.get_cpu_pin_aggregated().items():
                if is_pinned:
                    if cpuid not in tracking: raise ValueError('VM', vm.get_name(), 'is pinned to forbidden core', cpu, ':', vm.get_cpu_pin_aggregated())
                    tracking[cpuid].append(vm)
        return tracking

    def build_specific_tracker_dict(self):
        """Return a dict of free portion on each cpuid. Must be reimplemented
        ----------
        """
        raise NotImplementedError()

    def update_tracker(self):
        """Update tracking dicts. Must be reimplemented
        ----------
        """
        raise NotImplementedError()

    def available_resources(self):
        """Return available resources. Must be reimplemented
        ----------
        """
        raise NotImplementedError()

class AllocationTrackerNaive(AllocationTracker):
    """
    The NaiveTracker takes the following hypothesis : A VM cannot be pinned to a physical core with more than $(n-1)$ VM, $n$ being its oversubscription ratio
    So, a VM with r=2 can be pinned to a physical core with no more than 1 other VM, no matter its cpuset.
    ...

    Public Methods reimplemented/introduced
    -------
    build_specific_tracker_dict()
        Return a dict of free portion on each cpuid
    """

    def __init__(self, **kwargs):
        additional_attributes = []
        for req_attribute in additional_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', additional_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        super().__init__(**kwargs)

    def build_specific_tracker_dict(self):
        """Return a dict of free portion on each cpuid
        ----------
        """
        tracking = dict()
        for cpu, vm_list in self.generic_tracking.items():
            tracking[cpu] = 1
            for vm in vm_list: tracking[cpu]-= (1/vm.get_cpu_ratio())
            if tracking[cpu] < 0: raise ValueError('cpu', cpu, 'does not respect VM oversubscription constraints')
        return tracking

class AllocationTrackerPooled(AllocationTracker):
    """
    TODO
    ...

    Public Methods reimplemented/introduced
    -------
    build_specific_tracker_dict()
        Return a dict of free portion on each cpuid
    """

    def __init__(self, **kwargs):
        additional_attributes = []
        for req_attribute in additional_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', additional_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        super().__init__(**kwargs)

    def build_specific_tracker_dict(self):
        """Return a dict of free portion on each cpuid
        ----------
        """
        return 'todo'