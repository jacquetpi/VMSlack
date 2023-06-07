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

    def count_res(self):
        """Count resources in subset
        ----------

        Returns
        -------
        count : int
            number of resources
        """
        return len(self.res_list)

    def add_consumer(self, res):
        """Add a consumer to subset
        ----------

        Parameters
        ----------
        res : object
            The consumer to add
        """
        self.consumer_list.append(res)

    def remove_consumer(self, res):
        """Remove a consumer from subset
        ----------

        Parameters
        ----------
        res : object
            The consumer to remove
        """
        self.consumer_list.remove(res)

    def count_consumer(self):
        """Count consumers in subset
        ----------

        Returns
        -------
        count : int
            number of consumers
        """
        return len(self.consumer_list)

class SubsetCollection(object):
    """
    A SubsetCollection is a collection of Subset
    ...

    Attributes
    ----------
    subset_list : list
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
        self.subset_list = list()

    def add_subset(self, subset : Subset):
        """Add a subset to collection
        ----------

        Parameters
        ----------
        res : Subset
            The subset to add
        """
        self.subset_list.append(subset)

    def remove_subset(self, subset : Subset):
        """Remove a subset from collection
        ----------

        Parameters
        ----------
        res : Subset
            The subset to remove
        """
        self.subset_list.remove(subset)

    def count_subset(self):
        """Count subset in collection
        ----------

        Returns
        -------
        count : int
            number of consumers
        """
        return len(self.subset_list)

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