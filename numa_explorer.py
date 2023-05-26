from os import listdir
from os.path import isfile, join
import re

class numa_explorer:
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
        self.fs_folder = '/sys/devices/system/cpu/'
        self.fs_topology = '/topology'

    def explore(self):
        """Retrieve numa distances data as a dict
        ----------

        Returns
        -------
        numa_topology : dict
            dict of numa distances
        """
        topology_list = self.__retrieve_topology_folder()
        # TODO: la distance entre siblings ne semble pa être affiché dans le procs, est-ce qu'il est ailleurs?

    def __retrieve_topology_folder(self):
        """Retrieve the list of topology folder associated to each cpu conform to to_include, to_exclude attribute list
        ----------

        Returns
        -------
        folders : str
            list of topology folders  
        """
        regex = '^cpu[0-9]+$'
        cpu_found = [int(re.sub("[^0-9]", '', f)) for f in listdir(self.fs_folder) if not isfile(join(self.fs_folder, f)) and re.match(regex, f)]
        cpu_conform = [core for core in cpu_found if (core not in self.to_exclude) and (not self.to_include or core in self.to_include)]
        return [self.fs_folder + 'cpu' + str(cpu) + self.fs_topology for cpu in set(cpu_conform)]

if __name__ == '__main__':
    t = numa_explorer()
    t.explore()