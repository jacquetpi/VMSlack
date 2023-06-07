from schedulerlocal.subset.subset import SubsetCollection, CpuSubset, MemSubset
from schedulerlocal.subset.subsettracker import SubsetTracker, SubsetTrackerNaive

class SubsetManager(object):
    """
    A SubsetManager is an object in charge of determining appropriate subset collection
    ...

    Attributes
    ----------
    subset_collection : SubsetCollection
        collection of subset

    Public Methods
    -------
    build_initial_subset()
        Initiate collection object
    """

    def __init__(self, **kwargs):
        self.collection = SubsetCollection()
        self.build_initial_subset()

    def build_initial_subset(self):
        """Initialize subset Collection
        ----------
        """
        raise NotImplementedError() 

class CpuSubsetManager(SubsetManager):
    """
    A CpuSubsetManager is an object in charge of determining appropriate CPU subset collection
    ...

    Attributes
    ----------
    subset_collection : SubsetCollection
        collection of subset

    Public Methods reimplemented/introduced
    -------
    build_initial_subset()
        Initiate collection object
    """
    def __init__(self, **kwargs):
        req_attributes = ['cpuset', 'connector', 'distance_max']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        super().__init__(**kwargs)

    def build_initial_subset(self):
        """Initialize subset Collection
        ----------
        """
        cpu_subset = CpuSubset()
        for cpu in self.cpuset.get_cpu_list():
            cpu_subset.add_res(cpu_subset)
        self.collection.add_subset(cpu_subset)

class MemSubsetManager(SubsetManager):
    """
    A MemSubsetManager is an object in charge of determining appropriate Memory subset collection
    /!\ : out of scope of this paper. We just expose memory as a single package
    ...

    Attributes
    ----------
    subset_collection : SubsetCollection
        collection of subset

    Public Methods reimplemented/introduced
    -------
    build_initial_subset()
        Initiate collection object
    """
    def __init__(self, **kwargs):
        req_attributes = ['memset']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        super().__init__(**kwargs)

    def build_initial_subset(self):
        """Initialize subset Collection
        ----------
        """
        mem_subset = MemSubset()
        mem_subset.add_res((0, self.memset.get_allowed()))
        self.collection.add_subset(mem_subset)

class SubsetManagerPool(object):
    """
    A SubsetManagerPool is a pool of SubsetManager
    It is for now composed of a CpuSubsetManager and a MemSubsetManager
    /!\ Mem is out of scope of this paper. We just expose memory as a single package
    ...

    Attributes
    ----------
    cpu_subset_manager : CpuSubsetManager
        Cpu subset manager
    mem_subset_manager : MemSubsetManager
        Mem subset manager

    Public Methods
    -------
    iteration()
        Manage iteration
    """

    def __init__(self, **kwargs):
        req_attributes = ['cpuset', 'memset']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        self.cpu_subset_manager = CpuSubsetManager(cpuset=self.cpuset, distance_max=50)
        self.mem_subset_manager = MemSubsetManager(memset=self.memset)

    def iterate(self):
        print('cpuset', getattr(self.cpu_subset_manager, 'collection').count_subset())
        print('memset', getattr(self.mem_subset_manager, 'collection').count_subset())