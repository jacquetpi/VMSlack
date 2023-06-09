from schedulerlocal.domain.domainentity import DomainEntity
from math import ceil, floor

class SubsetOversubscription(object):
    """
    A SubsetOversubscription class is in charge to apply a specific oversubscription mechanism to a given subset
    ...

    Public Methods
    -------
    get_available()
        Virtual resources available
    unused_resources_count()
        Return attributed physical resources which are unused
    get_additional_res_count_required_for_vm()
        Return count of additional physical resources needed to deploy a vm
    get_id()
        Return oversubscription id
    """
    def __init__(self, **kwargs):
        req_attributes = ['subset']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])

    def get_available(self):
        """Return the number of virtual resources unused
        ----------

        Returns
        -------
        available : int
            count of available resources
        """
        raise NotImplementedError()

    def unused_resources_count(self):
        """Return attributed physical resources which are unused
        ----------

        Returns
        -------
        unused : int
            count of unused resources
        """
        raise NotImplementedError()

    def get_id(self):
        """Return the oversubscription strategy ID
        ----------

        Returns
        -------
        id : str
           oversubscription id
        """
        raise NotImplementedError()

class SubsetOversubscriptionStatic(SubsetOversubscription):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        req_attributes = ['ratio']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])

    def get_available(self):
        """Return the number of virtual resource available
        ----------

        Returns
        -------
        available : int
            count of available resources
        """
        return (self.subset.get_capacity()*self.ratio) - self.subset.get_allocation()


    def unused_resources_count(self):
        """Return attributed physical resources which are unused
        ----------

        Returns
        -------
        unused : int
            count of unused resources
        """
        available_oversubscribed = self.get_available()
        unused_cpu = floor(available_oversubscribed/self.ratio)

        used_cpu = self.subset.get_capacity() - unused_cpu
        max_alloc = self.subset.get_max_consumer_allocation()
        if used_cpu < max_alloc:
             # Specific case: our unused count floor should not reduce the capacity below the maximum configuration observed
             # Avoid VM to be oversubscribed with themselves
            return max(0, floor(self.subset.get_capacity()-max_alloc))
    
        # Generic case
        return unused_cpu


    def get_additional_res_count_required_for_vm(self, vm : DomainEntity):
        """Return the number of additional physical resource required to deploy specified vm. 
        0 if no additional resources is required
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
        request    = self.subset.get_vm_allocation(vm) # Without oversubscription
        capacity   = self.subset.get_capacity() # Without oversubscription
        if capacity < request:
            return ceil(request-capacity) # otherwise, VM will be oversubscribed with itself
        available_oversubscribed = self.get_available()
        missing_oversubscribed   = (request - available_oversubscribed)
        missing_physical = ceil(missing_oversubscribed/self.ratio) if missing_oversubscribed > 0 else 0
        return missing_physical

    def get_id(self):
        """Return the oversubscription strategy ID
        ----------

        Returns
        -------
        id : str
           oversubscription id
        """
        return self.ratio

    def __str__(self):
        return 'static oc:' + str(self.ratio)