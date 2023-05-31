from json import JSONEncoder, dumps, load

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

    Public Methods
    -------
    compute_distance_to_cpu()
        Given another ServerCPU instance, compute the relative distance between them
    Getter/Setter

    """
    def __init__(self, **kwargs):
        req_attributes = ['cpu_id', 'numa_node', 'sib_smt', 'sib_cpu', 'cache_level', 'max_freq']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])

    def compute_distance_to_cpu(self, other_cpu, numa_distances : dict):
        """Convert the distance from a given CPU to the current CPU occurence based on Cache level, siblings and numa distances
        ----------

        Parameters
        ----------
        other_cpu : ServerCpu
            Other CPU to compare
        numa_distances : dict
            Numa distances as dict

        Returns
        -------
        distance : int
            Distance as integer
        """
        # Health check
        if self.get_cpu_id() == other_cpu.get_cpu_id(): raise ValueError('Cannot compute distance to itself')
        if len(self.get_cache_level()) != len(other_cpu.get_cache_level()):
            # If heterogenous cache level exists, be careful to distance step incrementation
            raise ValueError('Cannot manage heterogenous cache level between', self.get_cpu_id(), 'and', other_cpu.get_cache_level())

        # Init
        distance = 0
        step = 10

        # Test cache level
        for cache_level, cache_id in self.get_cache_level().items(): 
            distance+=step
            if cache_id == other_cpu.get_cache_level()[cache_level]:
                return distance # Match on given cache

        # Test siblings
        distance+=10
        if other_cpu.get_cpu_id() in self.sib_smt: # Very unlikely as they do not share cache
          return distance
        distance+=10
        if other_cpu.get_cpu_id() in self.sib_cpu:
          return distance

       # At this point, we consider CPU from different NUMA node, we therefore use retrieved NUMA distance
        distance+= numa_distances[self.get_numa_node()][other_cpu.get_numa_node()]
        return distance

    def get_cpu_id(self):
        """Return unique CPUID
        ----------
        """
        return self.cpu_id

    def get_numa_node(self):
        """Return numa node related to the CPU
        ----------
        """
        return self.numa_node

    def get_sib_smt(self):
        """Return CPUID of siblings SMT cores
        ----------
        """
        return self.sib_smt

    def get_sib_cpu(self):
        """Return CPUID of siblings socket cores
        ----------
        """
        return self.sib_cpu

    def get_cache_level(self):
        """Return dict of cacheid related to the CPU
        ----------
        """
        return self.cache_level

    def get_max_freq(self):
        """Return core max freq
        ----------
        """
        return self.max_freq

    def __str__(self):
        """Return string representation of the core
        ----------
        """
        return 'cpu' + str(self.get_cpu_id()) +\
            ' ' + str(self.get_max_freq()/1000) + 'Mhz' +\
            ' on numa node ' + str(self.get_numa_node()) +\
            ' with cache level id ' + str(self.get_cache_level()) + '\n'

class ServerCpuSetEncoder(JSONEncoder):
    """
    Class to specify on to convert ServerCpuSet to JSON
    ...

    Public Methods
    -------
    default():
        json conversion
    """

    def default(self, o):
        """Implements Conversion strategy
        ----------

        Parameters
        ----------
        o : object
            object to convert
        """
        if type(o) is not ServerCpuSet:
            return
        as_dict = dict(o.__dict__)
        as_dict['cpu_list'] = [element.__dict__ for element in o.__dict__['cpu_list']]
        return as_dict

class ServerCpuSet(object):
    """
    A class used to represent CPU configuration of a given node
    Proximity between CPU is considered based on a distance node
    ...

    Attributes
    ----------
    numa_distances : dict()
        Dictionary of numa node distances
    cpu_list : list
        List of CPU
    distances : dict()
        List of CPU

    Public Methods
    -------
    add_cpu():
        Add a cpu to the considered cpuset
    build_distances():
        Build relative distances of given cpuset
    dump_as_json():
        build object attributes in json file
    load_from_json():
        load object attributes from json file
    Getter/Setter
    """

    def __init__(self, **kwargs):
        self.numa_distances = kwargs['numa_distances'] if 'numa_distances' in kwargs else None
        self.cpu_list = kwargs['cpu_list'] if 'cpu_list' in kwargs else list()
        self.distances = kwargs['distances'] if 'distances' in kwargs else dict()

    def add_cpu(self, cpu : ServerCpu):
        """Add a ServerCpu object
        ----------

        Parameters
        ----------
        cpu : ServerCpu
            cpu to add
        """
        self.cpu_list.append(cpu)

    def build_distances(self):
        """For each CPU tuple possible in the cpuset, compute the distance based on Cache Level, siblings and numa distances
        Distances are ordered.
        ----------
        """
        if self.numa_distances is None:
            raise ValueError('Numa distances weren\'t previously set')
        self.distances = dict()
        for cpu in self.cpu_list:
            single_cpu_distances = dict()
            others_cpu = list(self.cpu_list)
            others_cpu.remove(cpu)
            for other_cpu in others_cpu:
                single_cpu_distances[other_cpu.get_cpu_id()] = cpu.compute_distance_to_cpu(other_cpu, self.numa_distances)
            # Reorder distances from the closest one to the farthest one 
            self.distances[cpu.get_cpu_id()] = {k:v for k, v in sorted(single_cpu_distances.items(), key=lambda item: item[1])}
        return self

    def dump_as_json(self, filename : str):
        """Dump current state in a json file
        ----------

        Parameters
        ----------
        filename : str
            json file to write
        """
        with open(filename, 'w') as f: 
            f.write(dumps(self, cls=ServerCpuSetEncoder))

    def load_from_json(self, filename : str):
        """Instantiate attributes from a json file
        ----------

        Parameters
        ----------
        filename : str
            json file to read

        Returns
        -------
        self : ServerCpuSet
            itself
        """
        with open(filename, 'r') as f: 
            raw_object = load(f)
            self.numa_distances = {int(k):v for k,v in raw_object['numa_distances'].items()}
            self.distances = {int(k):{int(kprime):vprime for kprime,vprime in v.items()} for k,v in raw_object['distances'].items()}
            self.cpu_list = list()
            for raw_cpu in raw_object['cpu_list']: self.cpu_list.append(ServerCpu(**raw_cpu))
        return self

    def get_cpu_list(self):
        """Return CPU list
        ----------
        """
        return self.cpu_list

    def set_cpu_list(self, cpu_list : list):
        """Set CPU list
        ----------
        """
        self.cpu_list = cpu_list

    def get_numa_distances(self):
        """Return numa distances as dict
        ----------
        """
        return self.numa_distances

    def set_numa_distances(self, numa_distances : dict):
        """Set numa distances
        ----------
        """
        self.numa_distances = numa_distances

    def get_distances(self):
        """Return distances (empty dict if they werent previously build with build_distances() method)
        ----------
        """
        return self.distances