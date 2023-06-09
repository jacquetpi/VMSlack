from schedulerlocal.domain.domainentity import DomainEntity
from math import ceil

class Subset(object):
    """
    A Subset is an arbitrary group of physical resources to which consumers (e.g. VMs) can be attributed
    ...

    Attributes
    ----------
    res_list : list
        List of physical resources
    consumer_list : list
        List of consumers

    Public Methods
    -------
    add_res()
        Add a resource to subset
    remove_res()
        Remove a resource from subset
    get_res()
        Get resources list
    count_res()
        Count resources in subset
    add_consumer()
        Add a consumer to subset
    remove_consumer()
        Remove a consumer from subset
    count_consumer()
        Count resources in subset
    """
    def __init__(self, **kwargs):
        req_attributes = ['oversubscription']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        opt_attributes = ['res_list', 'consumer_list']
        for opt_attribute in opt_attributes:
            opt_val = kwargs[opt_attribute] if opt_attribute in kwargs else list()
            setattr(self, opt_attribute, opt_val)

    def add_res(self, res):
        """Add a resource to subset
        ----------

        Parameters
        ----------
        res : object
            The resource to add
        """
        if res in self.res_list: raise ValueError('Cannot add twice a resource', res)
        self.res_list.append(res)

    def remove_res(self, res):
        """Remove a resource to subset
        ----------

        Parameters
        ----------
        res : object
            The resource to remove
        """
        self.res_list.remove(res)

    def get_res(self):
        """Get resources list
        ----------

        Return
        ----------
        res : list
            resources list
        """
        return self.res_list

    def count_res(self):
        """Count resources in subset
        ----------

        Returns
        -------
        count : int
            number of resources
        """
        return len(self.res_list)

    def add_consumer(self, consumer):
        """Add a consumer to subset. Should not be called directly. Use deploy() instead
        ----------

        Parameters
        ----------
        consumer : object
            The consumer to add
        """
        if consumer in self.consumer_list: raise ValueError('Cannot add twice a consumer', res)
        self.consumer_list.append(consumer)

    def remove_consumer(self, consumer):
        """Remove a consumer from subset
        ----------

        Parameters
        ----------
        consumer : object
            The consumer to remove
        """
        self.consumer_list.remove(consumer)

    def count_consumer(self):
        """Count consumers in subset
        ----------

        Returns
        -------
        count : int
            number of consumers
        """
        return len(self.consumer_list)

    def get_consumers(self):
        """Get consumers list
        ----------

        Return
        ----------
        consumers : list
            consumers list
        """
        return self.consumer_list

    def get_additional_res_count_required_for_vm(self, vm : DomainEntity):
        """Return the number of additional resource required to deploy specified vm. 0 if no additional resources is required
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        missing : int
            number of missing physical resources
        """
        request    = self.get_vm_allocation(vm) # Without oversubscription
        capacity   = self.get_capacity() # Without oversubscription
        allocation = self.get_allocation()   # Without oversubscription
        if capacity < request:
            return ceil(request-capacity) # otherwise, VM will be oversubscribed with itself
        available_oversubscribed = (capacity-allocation)*self.oversubscription
        missing_oversubscribed   = (request - available_oversubscribed)
        missing_physical = ceil(missing_oversubscribed/self.oversubscription) if missing_oversubscribed > 0 else 0
        return missing_physical

    def get_allocation(self):
        """Return allocation of subset (number of resources requested without oversubscription consideration)
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        allocation : int
            Sum of resources requested
        """
        allocation = 0
        for consumer in self.consumer_list: allocation+= self.get_vm_allocation(consumer)
        return allocation

    def get_vm_allocation(self, vm : DomainEntity):
        """Return allocation of a given VM. Resource dependant. Must be reimplemented
        Allocation : number of resources requested, without oversubscription consideration
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        allocation : int
            Number of resources requested by the VM
        """
        raise NotImplementedError()

    def get_capacity(self):
        """Return subset resource capacity. Resource dependant. Must be reimplemented
        Capacity : number of resources which can be used by VM

        Returns
        -------
        capacity : int
            Subset resource capacity
        """
        raise NotImplementedError()

    def deploy(self, vm : DomainEntity):
        """Deploy a VM on resources. Resource dependant. Must be reimplemented with a super call
        Raise an exception if not enough resources are available
        """
        available_oversubscribed = (self.get_capacity()-self.get_allocation())*self.oversubscription
        if available_oversubscribed < self.get_vm_allocation(vm): 
            raise ValueError('Not enough resources available to deploy', vm.get_name())
        self.add_consumer(vm)

class SubsetCollection(object):
    """
    A SubsetCollection is a collection of Subset
    ...

    Attributes
    ----------
    subset_dict : list
        List of subsets

    Public Methods
    -------
    add_subset()
        Add a subset
    remove_subset()
        Remove a resource from subset
    count_subset()
        Count resources in subset
    """

    def __init__(self, **kwargs):
        self.subset_dict = dict()

    def add_subset(self, id : float, subset : Subset):
        """Add a subset to collection
        ----------

        Parameters
        ----------
        res : Subset
            The subset to add
        """
        if id in self.subset_dict: raise ValueError('Subset id already exists')
        self.subset_dict[id] = subset

    def remove_subset(self, id : float):
        """Remove a subset from collection
        ----------

        Parameters
        ----------
        id : str
            The subset id to remove
        """
        if id not in self.subset_dict: raise ValueError('Subset id does not exist')
        del self.subset_dict[id]

    def get_subset(self, id : float):
        """Get a subset from collection
        ----------

        Parameters
        ----------
        res : Subset
            The subset id to get
        """
        if id not in self.subset_dict: raise ValueError('Subset id does not exist')
        return self.subset_dict[id]

    def contains_subset(self, id : float):
        """Check if specified subset id exists
        ----------

        Parameters
        ----------
        res : bool
            Subset presence
        """
        return (id in self.subset_dict)

    def count_subset(self):
        """Count subset in collection
        ----------

        Returns
        -------
        count : int
            number of consumers
        """
        return len(self.subset_dict)

    def get_capacity(self):
        """Return the capacity sum of all subsets
        ----------

        Returns
        -------
        capacity : int
            Overall subset capacity
        """
        capacity = 0
        for subset in self.subset_dict.values(): capacity += subset.get_capacity()
        return capacity

    def get_res(self):
        """Return a list of all subset resources concatened
        ----------

        Returns
        -------
        res : list
            subset resources concatened
        """
        res = list()
        for subset in self.subset_dict.values(): res.extend(subset.get_res())
        return res

    def __str__(self):
        return ''.join([str(v) for v in self.subset_dict.values()])

class CpuSubset(Subset):
    """
    A CpuSubset is an arbitrary group of physical CPU to which consumers (e.g. VMs) can be attributed
    ...

    Public Methods reimplemented/introduced
    -------
    todo()
        todo
    """

    def __init__(self, **kwargs):
        additional_attributes = []
        for req_attribute in additional_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', additional_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        super().__init__(**kwargs)

    def get_vm_allocation(self, vm : DomainEntity):
        """Return CPU allocation of a given VM without oversubscription consideration
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        allocation : int
            Number of resources requested by the VM
        """
        return vm.get_cpu()

    def get_capacity(self):
        """Return subset CPU capacity.
        Capacity : number of CPU which can be used by VM

        Returns
        -------
        capacity : int
            Subset CPU capacity
        """
        return self.count_res()

    def deploy(self, vm : DomainEntity):
        """Deploy a VM on CPU subset
        Raise an exception if not enough resources are available
        ----------
        
        Parameters
        ----------
        vm : DomainEntity
            The VM to consider
        """
        super().deploy(vm) 
        # Update vm pinning

    def __str__(self):
        return 'CpuSubset oc:' + str(self.oversubscription) + ' alloc:' + str(self.get_allocation()) + ' capacity:' + str(self.get_capacity()) +\
            ' res:' + str([str(cpu.get_cpu_id()) for cpu in self.get_res()]) +\
            ' vm:' + str([vm.get_name() for vm in self.get_consumers()])

class MemSubset(Subset):
    """
    A MemSubset is an arbitrary division of memory to which consumers (e.g. VMs) can be attributed
    ...

    Public Methods reimplemented/introduced
    -------
    todo()
        todo
    """

    def __init__(self, **kwargs):
        additional_attributes = []
        for req_attribute in additional_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', additional_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        super().__init__(**kwargs)

    def get_vm_allocation(self, vm : DomainEntity):
        """Return Memory allocation of a given VM without oversubscription consideration
        ----------

        Returns
        -------
        allocation : int
            Number of resources requested by the VM
        """
        return vm.get_mem(as_kb=False) # in MB

    def get_capacity(self):
        """Return subset memory capacity.
        Capacity : Amount of memory which can be used by VM

        Returns
        -------
        capacity : int
            Subset Memory capacity
        """
        capacity = 0
        for bound_inferior, bound_superior in self.res_list:
            capacity += (bound_superior-bound_inferior) 
        return capacity

    def deploy(self, vm : DomainEntity):
        """Deploy a VM on memory subset
        Raise an exception if not enough resources are available
        ----------
        
        Parameters
        ----------
        vm : DomainEntity
            The VM to consider
        """
        super().deploy(vm)
        # Nothing special to do on memory with libvirt

    def __str__(self):
        return 'MemSubset oc:' + str(self.oversubscription) + ' alloc:' + str(self.get_allocation()) + ' capacity:' + str(self.get_capacity()) +\
            ' res:' + str(['[' + str(mem_tuple[0]) + ';' + str(mem_tuple[1]) + ']' for mem_tuple in self.get_res()]) +\
            ' vm:' + str([vm.get_name() for vm in self.get_consumers()])