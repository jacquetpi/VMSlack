from os import listdir
from os.path import isfile, join, exists
import re
from servercpuset import ServerCpuSet, ServerCpu

class NumaExplorer:
    """
    A class used to retrieve Numa information of host
    ...

    Attributes
    ----------
    to_include : list (optional)
        If specified, only core of this list will be considered (default to all)
    to_exclude : list (optional)
        If specified, core from this list will be excluded (default to none)

    Public Methods
    -------
    explore():
       Test if a VM verify this workload profile constraints
    """

    def __init__(self, **kwargs):
        attributes = ['to_include', 'to_exclude']
        for attribute in attributes:
            setattr(self, attribute, kwargs[attribute] if attribute in kwargs else list())
        self.fs_cpu           = '/sys/devices/system/cpu/'
        self.fs_cpu_topology  = '/topology'
        self.fs_cpu_cache     = '/cache/index'
        self.fs_cpu_maxfreq   = '/cpufreq/cpuinfo_max_freq'
        self.fs_numa          = '/sys/devices/system/node/'
        self.fs_numa_distance = '/distance'

    def build_cpuset(self):
        """Retrieve numa distances data as a dict
        ----------

        Returns
        -------
        numa_topology : dict
            dict of numa distances
        """
        cpuset = ServerCpuSet()
        cpu_list = self.__retrieve_cpu_list()
        for cpu in cpu_list: cpuset.add_cpu(self.__read_cpu(cpu, cpu_list))
        numa_distances = self.__read_numa_distance()
        cpuset.build(numa_distances=numa_distances)
        return cpuset

    def __retrieve_cpu_list(self):
        """Retrieve the list of cpu id conform to to_include and to_exclude attributes list
        ----------

        Returns
        -------
        folders : str
            list of topology folders  
        """
        regex = '^cpu[0-9]+$'
        cpu_found = [int(re.sub("[^0-9]", '', f)) for f in listdir(self.fs_cpu) if not isfile(join(self.fs_cpu_topology, f)) and re.match(regex, f)]
        cpu_conform = [core for core in cpu_found if (core not in self.to_exclude) and (not self.to_include or core in self.to_include)]
        cpu_conform.sort()
        return cpu_conform

    def __read_cpu(self, cpu : int, conform_cpu_list : list):
        """Retrieve numa distances data as a dict
        ----------

        Returns
        -------
        cpu_topology : dict
            dict of numa distances
        """
        conform_cpu_list_copy = list(set(conform_cpu_list))
        if cpu in conform_cpu_list_copy: del conform_cpu_list_copy[cpu]

        numa_node, sib_smt, sib_cpu = self.__read_cpu_topology(cpu, conform_cpu_list_copy)
        cache_level = self.__read_cpu_cache(cpu)
        max_freq = self.__read_cpu_maxfreq(cpu)

        return ServerCpu(cpu_id=cpu,\
            numa_node=numa_node, sib_smt=sib_smt, sib_cpu=sib_cpu,\
            cache_level=cache_level,\
            max_freq=max_freq)

    def __read_cpu_topology(self, cpu : int, conform_cpu_list : list):
        topology_folder = self.fs_cpu + 'cpu' + str(cpu) + self.fs_cpu_topology
        with open(topology_folder + '/physical_package_id', 'r') as f:
            socket_id = int(f.read())
        with open(topology_folder + '/thread_siblings_list', 'r') as f:
            sib_smt_list = [sibling_smt for sibling_smt in self.__convert_text_to_list(f.read()) if (sibling_smt != cpu) and sibling_smt in conform_cpu_list]
        with open(topology_folder + '/core_siblings_list', 'r') as f:
            sib_cpu_list = [sibling_cpu for sibling_cpu in self.__convert_text_to_list(f.read()) if (sibling_cpu != cpu) and sibling_cpu in conform_cpu_list]
        return socket_id, sib_smt_list, sib_cpu_list

    def __read_cpu_cache(self, cpu : int):
        cache_level = 0
        cache_dict = dict()
        while(True):
            cache_file = self.fs_cpu + 'cpu' + str(cpu) + self.fs_cpu_cache + str(cache_level) + '/id'
            if not exists(cache_file): break
            with open(cache_file , 'r') as f:
                cache_dict[cache_level] = int(f.read())
            cache_level+=1
        return cache_dict

    def __read_cpu_maxfreq(self, cpu : int):
        maxfreq_file = self.fs_cpu + 'cpu' + str(cpu) + self.fs_cpu_maxfreq
        with open(maxfreq_file , 'r') as f:
            maxfreq = int(f.read())
        return maxfreq

    def __read_numa_distance(self):
        numa_index = 0
        numa_dict = dict()
        while True:
            fs_distance = self.fs_numa + 'node' + str(numa_index) + self.fs_numa_distance
            if not exists(fs_distance): break
            with open(fs_distance, 'r') as f:
                numa_dict[numa_index] = f.read().replace('\n', '').split(' ')
            numa_index+=1
        return numa_dict

    def __convert_text_to_list(self, text : str):
        text_to_convert = text.replace('\n', '')
        if ',' in text_to_convert: 
            return [int(element) for element in text_to_convert.split(',')]
        elif '-' in text_to_convert:
            left_member = int(text_to_convert[:text_to_convert.find('-')])
            right_member = int(text_to_convert[text_to_convert.find('-')+1:])
            return list(range(left_member, right_member))
        else:
            return list(int(text_to_convert))

if __name__ == '__main__':
    t = NumaExplorer()
    t.build_cpuset()