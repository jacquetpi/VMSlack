import libvirt
from schedulerlocal.domain.libvirtxmlmodifier import xmlDomainNuma, xmlDomainMetaData
from schedulerlocal.domain.domainentity import DomainEntity

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
        self.cache_entity = dict()
        
    def get_vm_alive(self):
        """Retrieve list of VM being running currently as libvirt object
        ----------

        Returns
        -------
        vm_alive : list
            list of virDomain
        """
        return [self.conn.lookupByID( vmid ) for vmid in self.conn.listDomainsID()]

    def get_vm_alive_as_entity(self):
        """Retrieve list of VM being running currently as DomainEntity object
        ----------

        Returns
        -------
        vm_alive : list
            list of DomainEntity
        """ 
        return [self.convert_to_entitydomain(virDomain=vm_virDomain) for vm_virDomain in self.get_vm_alive()]

    def get_vm_shutdown(self):
        """Retrieve list of VM being shutdown currently as libvirt object
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
            domain_xml = xmlDomainNuma(xml_as_str=domain.XMLDesc())
            print(domain_xml.convert_to_str_xml())
            #self.conn.defineXML(domain_xml.convert_to_str_xml())

    def convert_to_entitydomain(self, virDomain : libvirt.virDomain, force_update = False):
        """Convert the libvirt virDomain object to the domainEntity domain
        ----------

        Parameters
        ----------
        virDomain : libvirt.virDomain
            domain to be converted
        force_update : bool
            Force update of cache

        Returns
        -------
        domain : DomainEntity
            domain as DomainEntity object
        """
        # Cache management
        uuid = virDomain.UUID()
        if (not force_update) and uuid in self.cache_entity: return self.cache_entity[uuid]
        # General info
        name = virDomain.name()
        mem = virDomain.maxMemory()
        cpu = virDomain.maxVcpus()
        cpu_pin = virDomain.vcpuPinInfo()
        # Custom metadata
        xml_manager = xmlDomainMetaData(xml_as_str=virDomain.XMLDesc())
        xml_manager.convert_to_object()
        if xml_manager.updated() : 
            self.conn.defineXML(xml_manager.convert_to_str_xml()) # Will only be applied after a restart
            print('Warning, no oversubscription found on domain', name, ': defaults were generated')
        cpu_ratio = xml_manager.get_oversub_ratios()['cpu']
        # Build entity
        self.cache_entity[uuid] = DomainEntity(uuid=uuid, name=name, mem=mem, cpu=cpu, cpu_pin=cpu_pin, cpu_ratio=cpu_ratio)
        return self.cache_entity[uuid]

    def cache_purge(self):
        """Purge cache associating VM uuid to their domainentity representation
        ----------
        """
        del self.cache_entity
        self.cache_entity = dict()

    def __del__(self):
        """Clean up actions
        ----------
        """
        self.conn.close()