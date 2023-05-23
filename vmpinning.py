import libvirt, getopt, sys
from dotenv import load_dotenv
from xml.dom import minidom

def connect_to_libvirt():
    url = 'qemu:///system'
    conn = libvirt.open(url)
    if not conn:
        raise SystemExit('Failed to open connection to ' + url)
    return conn

class xmlObject(object):

    def __init__(self, xml = None):
        self.raw = None
        if xml is not None: self.raw = xml
        if self.raw is not None: self.convert_to_object()

    def convert_to_object(self):
        raise NotImplementedError()

    def convert_to_xml(self):
        raise NotImplementedError()

    def get_dom(self):
        dom_root = self.parse()
        return dom_root, self.get_dom_specific(dom_root)

    def get_dom_specific(self, dom_root : minidom.Document):
        raise NotImplementedError()

    def parse(self):
        return minidom.parseString(self.raw)

class xmlDomainCpuNumaCell(xmlObject):

    def __init__(self, xml = None):
        super().__init__(xml)
        
    def generate_default(self, id : int, cpu_count : int):
        return self

    def convert_to_object(self):
        doom_root, dom_topology = self.__get_dom()
        for attribute in self._topology_attributes : self.topology[attribute] = dom_topology.getAttribute(attribute)

    def convert_to_xml(self):
        return 'todo'

    def __str__(self):
        return 'todo'

class xmlDomainCpu(xmlObject):

    def __init__(self, xml = None):
        self._topology_attributes = ['sockets', 'dies', 'cores', 'threads']
        self.topology = dict()
        for attribute in self._topology_attributes : self.topology[attribute] = None
        self.numa_cells = list()
        super().__init__(xml)
        
    def convert_to_object(self):
        doom_root, dom_topology = self.get_dom()
        for attribute in self._topology_attributes : self.topology[attribute] = dom_topology.getAttribute(attribute)

        dom_numa_list = dom_topology.getElementsByTagName('numa')
        if len(dom_numa_list)<1:
            print("Warning, no NUMA configuration found, generating default")
            count = self.get_cpu_count()
            for id in range(count): self.numa_cells.append(xmlDomainCpuNumaCell().generate_default(id=id, cpu_count=count))
        elif len(dom_numa_list)==1:
            dom_numa = dom_numa_list[0]
            dom_numa_cell_list = dom_numa.getElementsByTagName('cell')
            for dom_numa_cell in dom_numa_cell_list: self.numa_cells.append(xmlDomainCpuNumaCell(dom_numa_cell))
        else: 
            raise ValueError("Incorrect number of numa node in xml", len(dom_numa_list))
    
    def get_topology_as_dict(self):
        return self.topology

    def set_topology_as_dict(self, topology):
        self.topology=topology

    def convert_to_xml(self):
        doom_root, dom_topology = self.get_dom()
        for attribute in self._topology_attributes : dom_topology.setAttribute(attribute, self.topology[attribute])
        return doom_root.toxml()

    def get_cpu_count(self):
        count=0
        for attribute in self._topology_attributes: 
            if attribute != 'dies': count+= int(self.topology[attribute])
        return count

    def get_dom_specific(self, dom_root : minidom.Document):
        dom_cpu_list =  dom_root.getElementsByTagName("cpu")
        if len(dom_cpu_list) != 1: raise ValueError("Incorrect number of cpu node in xml", len(dom_cpu_list))
        dom_cpu = dom_cpu_list[0]
        
        dom_topology_list = dom_cpu.getElementsByTagName('topology')
        if len(dom_topology_list) != 1: raise ValueError("Incorrect number of topology node in xml", len(dom_topology_list))
        dom_topology = dom_topology_list[0]

        return dom_topology

    def __str__(self):
        return ' '.join([attribute + ':' + str(self.topology[attribute]) for attribute in self._topology_attributes]) + '\n' +\
             ' '.join(['  ' + numa_cell.__str__() for numa_cell in self.numa_cells])

    def live_change(self, domain):
        print(domain.emulatorPinInfo())
        #domain.pinEmulator()
        print(domain.ioThreadInfo())
        #domain.pinIOThread()
        print(domain.vcpuPinInfo())
        #domain.pinVcpu()
        print(domain.vcpusFlags())
        #domain.pinVcpuFlags()
        print(domain.numaParameters())
        #domain.setNumaParameters()

if __name__ == '__main__':

    short_options = 'h'
    long_options = ['help']

    try:
        arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print (str(err)) # Output error, and return with an error code
        sys.exit(2)
    for current_argument, current_value in arguments:
        if current_argument in ('-h', '--help'):
            print('python3 vmpinning.py [--help]')
            sys.exit(0)

    try:    

        conn = connect_to_libvirt()
        vm_shutdown = [conn.lookupByName(name) for name in conn.listDefinedDomains()]
        vm_alive    = [conn.lookupByID( vmid ) for vmid in conn.listDomainsID()]
        for domain in vm_alive:
            
            requested_topology = {'sockets':1, 'dies':1, 'cores':1, 'threads':2}
            attributes = list(requested_topology.keys())

            domain_xml = xmlDomainCpu(xml=domain.XMLDesc())
            print(domain_xml)
            conn.defineXML(domain_xml.convert_to_xml())

        conn.close()

    except KeyboardInterrupt:
        print("Program interrupted")