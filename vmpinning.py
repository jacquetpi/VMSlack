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

    def __init__(self, xml_as_document = None, xml_as_str = None):
        self.xml = None
        if   xml_as_document is not None: self.xml = xml_as_document
        elif xml_as_str     is not None: self.xml = self.parse(xml_as_str)
        if self.xml is not None: self.convert_to_object()

    def convert_to_object(self):
        raise NotImplementedError()

    def convert_to_str_xml(self):
        dom_root, dom_targeted = self.get_all_dom() 
        self.update_dom(dom_targeted)
        return dom_root.toprettyxml()

    def update_dom(self, dom_targeted : minidom.Document):
        raise NotImplementedError()

    def get_all_dom(self):
        return self.get_dom_root(), self.get_dom_specific(self.xml)

    def get_dom_root(self):
        return self.xml

    def get_dom_specific(self, dom_root : minidom.Document): # default to cpu node
        dom_cpu_list =  dom_root.getElementsByTagName("cpu")
        if len(dom_cpu_list) != 1: raise ValueError("Incorrect number of cpu node in xml", len(dom_cpu_list))
        return dom_cpu_list[0]

    def parse(self, to_be_parsed : str):
        return minidom.parseString(to_be_parsed)

class xmlDomainCpuNumaCell(xmlObject):

    def __init__(self, xml_as_document = None, xml_as_str = None, id : int = None, cpu_count : int = None,):
        self.id=id
        self.cpu_count=cpu_count # to generate default
        self._cell_attributes = ['id', 'cpus']
        #self._cell_attributes = ['id', 'cpus', 'memory', 'unit']
        self.cells = dict()
        self.distances = dict()
        super().__init__(xml_as_document=xml_as_document,xml_as_str=xml_as_str)

    def initialize_default_cell(self, dom_root : minidom.Document):
        # Initialize object attribute
        self.cells = dict()
        self.cells['id'] = str(self.id)
        self.cells['cpus'] = str(self.id)
        self.cells['memory'] = '512000'
        self.cells['unit'] = 'KiB'
        for index in range(self.cpu_count): 
            if index == self.id:
                self.distances[index]=10
            else:
                self.distances[index]=20

        # Initialize xml cell
        dom_cell =  dom_root.createElement('cell')
        for attribute in self._cell_attributes: dom_cell.setAttribute(attribute, self.cells[attribute])
        # Initialize xml cell siblings values
        dom_distances =  dom_root.createElement('distances')
        dom_cell.appendChild(dom_distances)
        for distance_id, distance_val in self.distances.items():
            dom_sibling =  dom_root.createElement('sibling')
            dom_sibling.setAttribute('id', str(distance_id))
            dom_sibling.setAttribute('value', str(distance_val))
            dom_distances.appendChild(dom_sibling)
        return dom_cell

    def convert_to_object(self):
        dom_cell = self.get_dom_specific(self.get_dom_root())
        for attribute in self._cell_attributes: 
            self.cells[attribute] = dom_cell.getAttribute(attribute)
        
        dom_distances_list = dom_cell.getElementsByTagName('distances')
        if len(dom_distances_list)<1:
            print("Warning, no distances found")
        elif len(dom_distances_list)==1:
            dom_distances = dom_distances_list[0]
            dom_sibling_list = dom_distances.getElementsByTagName('sibling')
            for dom_sibling in dom_sibling_list:
                self.distances[dom_sibling.getAttribute('id')] = dom_sibling.getAttribute('value')
        else:
            raise ValueError("Incorrect number of 'distances' node in xml", len(dom_distances_list))

    def update_dom(self, dom_targeted : minidom.Element):
        for attribute in self._cell_attributes : dom_targeted.setAttribute(attribute, self.cells[attribute])

    def get_dom_specific(self, dom_root : minidom.Document): # Return cell node (create it if not present)
        dom_cpu = super().get_dom_specific(dom_root)

        dom_numa_list = dom_cpu.getElementsByTagName('numa')
        dom_numa = None
        if len(dom_numa_list) == 0:
            dom_numa =  dom_root.createElement('numa')
            dom_cpu.appendChild(dom_numa)
        else:
            dom_numa =  dom_numa_list[0]

        if dom_numa == None: raise ValueError("Incorrect number of 'topology' node in xml", len(dom_numa_list))
        return self.__get_dom_cell_in_numa(dom_root, dom_numa)

    def __get_dom_cell_in_numa(self, dom_root : minidom.Document, dom_numa : minidom.Element):
        dom_cell_list = dom_numa.getElementsByTagName('cell')

        dom_cell = None
        for dom_cell_tested in dom_cell_list:
            if dom_cell_tested.getAttribute('id') == str(self.id):
                dom_cell = dom_cell_tested

        if dom_cell == None:
            dom_cell = self.initialize_default_cell(dom_root)
            dom_numa.appendChild(dom_cell)

        return dom_cell

    def __str__(self):
        return 'cell id=' + str(self.cells['id']) +' cpus=' + str(self.cells['cpus']) + ' memory=' + str(self.cells['memory']) +' unit=' + str(self.cells['unit']) + ' distances: ' + str(self.distances) + '\n'

class xmlDomainCpu(xmlObject):

    def __init__(self, xml_as_document = None, xml_as_str = None):
        self._topology_attributes = ['sockets', 'dies', 'cores', 'threads']
        self.topology = dict()
        for attribute in self._topology_attributes : self.topology[attribute] = None
        self.numa_cells = list()
        super().__init__(xml_as_document=xml_as_document,xml_as_str=xml_as_str)

    def convert_to_object(self):
        dom_root, dom_topology = self.get_all_dom()
        for attribute in self._topology_attributes : self.topology[attribute] = dom_topology.getAttribute(attribute)

        dom_numa_list = dom_topology.getElementsByTagName('numa')
        if len(dom_numa_list)<1:
            print("Warning, no NUMA configuration found, generating default")
            count = self.get_cpu_count()
            for id in range(count): self.numa_cells.append(xmlDomainCpuNumaCell(xml_as_document=dom_root, id=id, cpu_count=count))
        elif len(dom_numa_list)==1:
            dom_numa = dom_numa_list[0]
            dom_numa_cell_list = dom_numa.getElementsByTagName('cell')
            for dom_numa_cell in dom_numa_cell_list: self.numa_cells.append(xmlDomainCpuNumaCell(xml_as_document=dom_root))
        else:
            raise ValueError("Incorrect number of 'numa' node in xml", len(dom_numa_list))

    def get_topology_as_dict(self):
        return self.topology

    def set_topology_as_dict(self, topology):
        self.topology=topology

    def get_cpu_count(self):
        count=1
        for attribute in self._topology_attributes:
            if attribute != 'dies': count*= int(self.topology[attribute])
        return count

    def update_dom(self, dom_targeted : minidom.Element):
        if dom_targeted==None: dom_targeted=self.get_dom_specific()
        # Update current object
        for attribute in self._topology_attributes : dom_targeted.setAttribute(attribute, self.topology[attribute])
        # Update child objects
        for numa_cell in self.numa_cells: numa_cell.update_dom(dom_targeted=numa_cell.get_dom_specific(numa_cell.get_dom_root()))
        return dom_targeted

    def get_dom_specific(self, dom_root : minidom.Document): # Return topology node
        dom_cpu = super().get_dom_specific(dom_root)

        dom_topology_list = dom_cpu.getElementsByTagName('topology')
        if len(dom_topology_list) != 1: raise ValueError("Incorrect number of 'topology' node in xml", len(dom_topology_list))
        return dom_topology_list[0]

    def __str__(self):
        return ' '.join([attribute + ':' + str(self.topology[attribute]) for attribute in self._topology_attributes]) + '\n' +\
             ''.join(['  ' + numa_cell.__str__() for numa_cell in self.numa_cells])

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

            domain_xml = xmlDomainCpu(xml_as_str=domain.XMLDesc())

            print(domain_xml.convert_to_str_xml())
            #conn.defineXML(domain_xml.convert_to_str_xml())

        conn.close()

    except KeyboardInterrupt:
        print("Program interrupted")
