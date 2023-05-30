import math

class ServerCpu(object):
    """
    A class used to represent a CPU
    ...

    Attributes
    ----------
    cpu_id : int
        ID of CPU
    numa_node : int
        ID of numa node
    sib_smt : list
        List of CPU id sharing the cpu in SMT
    sib_cpu : list
        List of CPU id sharing the numa node
    cache_level :
        Dict of cache level identifier associated to the CPU
    max_freq :
        Max CPU frequency
    
    """
    def __init__(self, **kwargs):
        req_attributes = ['cpu_id', 'numa_node', 'sib_smt', 'sib_cpu', 'cache_level', 'max_freq']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
            print(kwargs[req_attribute])
        print("####")
    
    def get_cpu_id(self):
        return self.cpu_id

    def get_numa_node(self):
        return self.numa_node

    def get_sib_smt(self):
        return self.sib_smt

    def get_sib_cpu(self):
        return self.sib_cpu

    def get_cache_level(self):
        return self.cache_level

    def get_max_freq(self):
        return self.max_freq

    def compute_distance_to_cpu(self, other_cpu):
        if self.get_cpu_id() == other_cpu.get_cpu_id(): raise ValueError('Cannot compute distance to itself')
        distance = 10
        step = 10
        # Test cache level
        for cache_level, cache_id in self.get_cache_level().items():
            if cache_level not in other_cpu.get_cache_level(): break
            if cache_id == other_cpu.get_cache_level()[cache_level]:
                # Match on given cache
                return distance
            distance+=step

        if self.get_numa_node() != other_cpu.get_numa_node():
            return math.inf

        raise ValueError('Impossible to compute distance between CPU', self.get_cpu_id(), other_cpu.get_cpu_id())

    def __str__(self):
        return 'cpu' + str(self.get_cpu_id()) +\
            ' ' + str(self.get_max_freq()/1000) + 'Mhz' +\
            ' on numa node ' + str(self.get_numa_node()) +\
            ' with cache level id ' + str(self.get_cache_level()) + '\n'

class ServerCpuSet(object):
    """
    A class used to represent CPU configuration of a given node
    Proximity between CPU is considered based on a distance node
    ...

    Attributes
    ----------
    cpu_list : list
        List of CPU

    Public Methods
    -------
    add_cpu():
        Add a cpu to the considered cpuset

    build():
        Build relative distances of given cpuset
    """

    def __init__(self):
        self.cpu_list = list()


    def add_cpu(self, cpu : ServerCpu):
        self.cpu_list.append(cpu)

    def build(self, numa_distances : dict):
        distances = dict()
        for cpu in self.cpu_list:
            distances[cpu.get_cpu_id()] = dict()
            others_cpu = list(self.cpu_list)
            others_cpu.remove(cpu)
            for other_cpu in others_cpu:
                distance = cpu.compute_distance_to_cpu(other_cpu)
                print(cpu, other_cpu, distance)
                distances[cpu.get_cpu_id()][other_cpu.get_cpu_id()] = distance