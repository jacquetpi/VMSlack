import libvirt
from schedulerlocal.domain.libvirtxmlmodifier import xmlDomainCpu

class LibvirtConnector(object):
    """
    A class used as an interface with libvirt API
    ...

    Attributes
    ----------
    url : str
        hypervisor url

    """


    def __init__(self, **kwargs):
        req_attributes = ['url']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        # Connect to libvirt url    
        self.conn = libvirt.open(self.url)
        if not self.conn:
            raise SystemExit('Failed to open connection to ' + self.url)
        
    def get_vm_alive(self):
        """Retrieve list of VM being running currently
        ----------

        Returns
        -------
        vm_alive : list
            list of virDomain
        """
        return [self.conn.lookupByID( vmid ) for vmid in self.conn.listDomainsID()]

    def get_vm_shutdown(self):
        """Retrieve list of VM being shutdown currently
        ----------

        Returns
        -------
        vm_shutdown : list
            list of virDomain
        """
        return [self.conn.lookupByName(name) for name in self.conn.listDefinedDomains()]

    def get_all_vm(self):
        """Retrieve list of all VM
        ----------

        Returns
        -------
        vm_list : list
            list of virDomain
        """
        vm_list = self.get_vm_alive()
        vm_list.extend(self.get_vm_shutdown())
        return vm_list

    def print_vm_topology(self):
        """Print all VM topology
        ----------

        """
        for domain in self.get_vm_alive():
            domain_xml = xmlDomainCpu(xml_as_str=domain.XMLDesc())
            print(domain_xml.convert_to_str_xml())
            #self.conn.defineXML(domain_xml.convert_to_str_xml())

    def __del__(self):
        self.conn.close()