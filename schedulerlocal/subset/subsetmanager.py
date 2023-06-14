from schedulerlocal.subset.subset import SubsetCollection, Subset, CpuSubset, MemSubset
from schedulerlocal.domain.domainentity import DomainEntity
from schedulerlocal.node.cpuexplorer import CpuExplorer
from schedulerlocal.node.memoryexplorer import MemoryExplorer

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
        Deploy a VM to the appropriate subset. Must be reimplemented
    """

    def __init__(self, **kwargs):
        req_attributes = ['connector', 'endpoint_pool']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        self.collection = SubsetCollection()
    
    def deploy(self, vm : DomainEntity):
        """Deploy a VM to the appropriate subset
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        success : bool
            Return success status of operation
        """
        if self.collection.contains_subset(self.get_appropriate_id(vm)):
            return self.__try_to_deploy_on_existing_subset(vm)
        return self.__try_to_deploy_on_new_subset(vm)

    def remove(self, vm : DomainEntity):
        """Remove a VM
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        success : bool
            Return success status of operation
        """
        subset_id = self.get_appropriate_id(vm)
        if not self.collection.contains_subset(subset_id): return False
        subset = self.collection.get_subset(subset_id)
        subset.remove_consumer(vm)
        self.shrink_subset(subset)
        return True

    def __try_to_deploy_on_existing_subset(self,  vm : DomainEntity):
        """Try to deploy a VM to an existing subset by extending it if required 
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        success : bool
            Return success status of operation
        """
        targeted_subset = self.collection.get_subset(self.get_appropriate_id(vm))
        # Check if subset has available space
        additional_res_required = targeted_subset.get_additional_res_count_required_for_vm(vm)
        if additional_res_required <= 0:
            # No missing space, can deploy the VM right away
            return targeted_subset.deploy(vm)
        else:
            # Missing space on subset, try to allocate more
            extended = self.try_to_extend_subset(targeted_subset, additional_res_required)
            if not extended: return False 
            return targeted_subset.deploy(vm) 

    def __try_to_deploy_on_new_subset(self, vm : DomainEntity):
        """Try to deploy a VM to a new subset
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        success : bool
            Return success status of operation
        """
        oversubscription = self.get_appropriate_id(vm)
        # Even in oversubscribed env, CPU should be on a pool having pCPU > vCPU to not be oversubscribed with itself
        subset = self.try_to_create_subset(initial_capacity=self.get_request(vm), oversubscription=oversubscription)
        if subset == None: return False
        self.collection.add_subset(oversubscription, subset)
        return subset.deploy(vm)

    def try_to_extend_subset(self,  subset : Subset, amount : int):
        """Try to extend subset resource by the specified amount. Resource dependant. Must be reimplemented
        ----------

        Parameters
        ----------
        subset : SubSet
            The targeted subset
        amount : int
            Resources requested

        Returns
        -------
        success : bool
            Return success status of operation
        """
        raise NotImplementedError()

    def try_to_create_subset(self,  initial_capacity : int, oversubscription : float):
        """Try to create subset with specified capacity. Resource dependant. Must be reimplemented
        ----------

        Parameters
        ----------
        initial_capacity : int
            Resources requested
        oversubscription : float
            Subset oversubscription

        Returns
        -------
        subset : Subset
            Return Subset created. None if failed. Resource dependant. Must be reimplemented
        """
        raise NotImplementedError()

    def get_appropriate_id(self, vm : DomainEntity):
        """For a given VM, a subset ID typically corresponds to its premium policy. Must be reimplemented
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        subset_id : float
            premium policy
        """
        raise NotImplementedError()

    def get_request(self, vm : DomainEntity):
        """For a given VM, return its resource request. Resource dependant. Must be reimplemented
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        request : int
            VM resource request
        """
        raise NotImplementedError()


    def shrink(self):
        """Reduce subset capacity based on current allocation
        ----------
        """
        for subset in self.collection.get_subsets(): self.shrink_subset(subset)

    def shrink_subset(self, subset : Subset = None):
        """Reduce subset capacity based on current allocation. Resource dependant. Must be reimplemented
        ----------

        Parameters
        ----------
        subset : Subset
            The subset to shrink
        """
        # Must be reimplemented
        if (subset.count_res() == 0) and (subset.count_consumer() ==0):
            self.collection.remove_subset(subset.get_id())
            del subset

    def get_current_resources_usage(self):
        """Get current usage of physical resources. Resource dependant. Must be reimplemented

        Returns
        -------
        usage : int
            Percentage [0:1]
        """
        raise NotImplementedError()

    def update_monitoring(self, timestamp : int):
        """Order a monitoring session on host and on each subset with specified timestamp key
        Use endpoint_pool to load and store from the appropriate location
        ----------

        Parameters
        ----------
        timestamp : int
            The timestamp key
        """
        # Update global data: Nothing is done live with it currently but data are dumped for post analysis
        data = self.endpoint_pool.load_global(timestamp=timestamp, subset_manager=self)
        # Update subset data
        self.collection.update_monitoring(timestamp=timestamp)

    def get_res_name(self):
        """Get resource name managed by ManagerSubset. Resource dependant. Must be reimplemented
        ----------

        Return
        ----------
        res : str
            resource name
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
    deploy()
        Deploy a VM to the appropriate CPU subset
    """
    def __init__(self, **kwargs):
        req_attributes = ['connector', 'cpuset', 'distance_max']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        self.cpu_explorer = CpuExplorer()
        super().__init__(**kwargs)

    def try_to_create_subset(self,  initial_capacity : int, oversubscription : float):
        """Try to create subset with specified capacity
        TODO: Simplify
        ----------

        Parameters
        ----------
        initial_capacity : int
            Resources requested (without oversubscription consideration)
        oversubscription : float
            Subset oversubscription

        Returns
        -------
        subset : Subset
            Return CpuSubset created. None if failed.
        """
        if initial_capacity <=0 : raise ValueError('Cannot create a subset with negative capacity', initial_capacity)
        
        # Starting point
        available_cpus_ordered = self.__get_farthest_available_cpus()
        if len(available_cpus_ordered) < initial_capacity: return None
        starting_cpu = available_cpus_ordered[0]
        cpu_subset = CpuSubset(oversubscription=oversubscription, connector=self.connector, cpu_explorer=self.cpu_explorer, endpoint_pool=self.endpoint_pool)
        cpu_subset.add_res(starting_cpu)

        initial_capacity-=1 # One was attributed
        if initial_capacity>0:
            available_cpus_ordered = self.__get_closest_available_cpus(cpu_subset) # Recompute based on chosen starting point
            for i in range(initial_capacity): cpu_subset.add_res(available_cpus_ordered[i])
        return cpu_subset

    def try_to_extend_subset(self, subset : CpuSubset, amount : int):
        """Try to extend subset cpu by the specified amount
        ----------

        Parameters
        ----------
        subset : SubSet
            The amount requested
        amount : int
            Resources requested

        Returns
        -------
        success : bool
            Return success status of operation
        """
        available_cpus_ordered = self.__get_closest_available_cpus(subset)
        if len(available_cpus_ordered) < amount: return None
        for i in range(amount): subset.add_res(available_cpus_ordered[i])
        return True

    def __get_closest_available_cpus(self, subset : CpuSubset):
        """Retrieve the list of available CPUs ordered by their average distance value closest to specified Subset
        ----------

        Parameters
        ----------
        subset : CpuSubset
            The subset requested

        Returns
        -------
        cpu_list : list
            List of available CPU ordered by their distance
        """
        cpuid_dict = {cpu.get_cpu_id():cpu for cpu in self.cpuset.get_cpu_list()}
        available_list = self.__get_available_cpus()
        allocated_list = subset.get_res()
        available_cpu_weighted = self.__get_available_cpus_with_weight(from_list=available_list, to_list=allocated_list, exclude_max=True)
        # Reorder distances from the closest one to the farthest one
        return [cpuid_dict[cpuid] for cpuid, v in sorted(available_cpu_weighted.items(), key=lambda item: item[1])]

    def __get_farthest_available_cpus(self):
        """When considering subset allocation. One may want to start from the farthest CPU possible
        This getter retrieve available CPUs and order them in a reverse order based on distance from current subsets CPUs
        ----------

        Returns
        -------
        ordered_cpu : list
            List of available CPU ordered in reverse by their distance
        """
        cpuid_dict = {cpu.get_cpu_id():cpu for cpu in self.cpuset.get_cpu_list()}
        available_list = self.__get_available_cpus()
        allocated_list = self.collection.get_res()
        available_cpu_weighted = self.__get_available_cpus_with_weight(from_list=available_list, to_list=allocated_list, exclude_max=False)
        # Reorder distances from the farthest one to the closest one
        return [cpuid_dict[cpuid] for cpuid, v in sorted(available_cpu_weighted.items(), key=lambda item: item[1], reverse=True)]

    def __get_available_cpus_with_weight(self, from_list : list, to_list : list, exclude_max : bool = True):
        """Computer the average distance of CPU presents in from_list to the one in to_list
        ----------

        Parameters
        ----------
        from_list : list
            list of ServerCPU
        to_list : list
            list of ServerCPU
        exclude_max : bool (optional)
            Should CPU having a distance value higher than the one fixed in max_distance attribute being disregarded
        
        Returns
        -------
        distance : dict
            Dict of CPUID (as key) with average distance being computed
        """
        computed_distances = dict()
        for available_cpu in from_list:
            total_distance = 0
            total_count = 0

            exclude_identical = False
            for subset_cpu in to_list: 
                if subset_cpu == available_cpu: 
                    exclude_identical = True
                    break

                distance = self.cpuset.get_distance_between_cpus(subset_cpu, available_cpu)
                if exclude_max and (distance >= self.distance_max): 
                    total_distance = -1
                    break

                total_distance+=distance
                total_count+=1

            if exclude_identical : continue
            if total_count <= 0: computed_distances[available_cpu.get_cpu_id()] = 0
            elif total_distance>=0: computed_distances[available_cpu.get_cpu_id()] = total_distance/total_count

        return computed_distances

    def __get_available_cpus(self):
        """Retrieve the list of CPUs without subset attribution
        ----------

        Returns
        -------
        cpu_list : list
            list of CPUs without attribution
        """
        allocated_cpu_list = self.collection.get_res()
        available_cpu_list = list()
        for cpu in self.cpuset.get_cpu_list(): 
            if cpu not in allocated_cpu_list: available_cpu_list.append(cpu)
        return available_cpu_list

    def shrink_subset(self, subset : CpuSubset):
        """Reduce subset capacity based on current allocation
        ----------

        Parameters
        ----------
        subset : Subset
            The subset to shrink
        """
        unused = subset.unused_resources_count()
        res_list = list(subset.get_res())
        last_index = len(res_list) - 1
        for count in range(unused): subset.remove_res(res_list[last_index-count])
        subset.sync_pinning()
        super().shrink_subset(subset)

    def get_appropriate_id(self, vm : DomainEntity):
        """For a given VM, get its appropriate subset ID (corresponds to its premium policy)
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        id : int
            Its oversubscription ratio as subset ID
        """
        return vm.get_cpu_ratio()

    def get_current_resources_usage(self):
        """Get usage of physical CPU resources

        Returns
        -------
        Usage : int
            Percentage [0:1]
        """
        return self.cpu_explorer.get_usage_global()

    def get_request(self, vm : DomainEntity):
        """For a given VM, return its CPU request
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        cpu : int
            CPU request of given VM
        """
        return vm.get_cpu()

    def get_res_name(self):
        """Get resource name managed by ManagerSubset
        ----------

        Return
        ----------
        res : str
            resource name
        """
        return 'cpu'

    def __str__(self):
        return 'CPUSubsetManager:\n' +  str(self.collection)

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
    deploy()
        Deploy a VM to the appropriate CPU subset
    """
    def __init__(self, **kwargs):
        req_attributes = ['connector', 'memset']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        self.mem_explorer = MemoryExplorer()
        super().__init__(**kwargs)

    def try_to_create_subset(self,  initial_capacity : int, oversubscription : float):
        """Try to create subset with specified capacity
        ----------

        Parameters
        ----------
        initial_capacity : int
            Resources requested
        oversubscription : float
            Subset oversubscription

        Returns
        -------
        subset : Subset
            Return MemSubset created. None if failed.
        """
        targeted_inf = 0
        for subset_tuple in self.collection.get_res():
            bound_inf, bound_sup = subset_tuple
            if bound_sup > targeted_inf: targeted_inf = bound_sup+1
        new_tuple = (targeted_inf, targeted_inf+initial_capacity)
        
        if not self.__check_capacity_bound(bounds=new_tuple): return None
        if not self.__check_overlap(new_tuple=new_tuple): return None

        mem_subset = MemSubset(oversubscription=oversubscription, connector=self.connector, endpoint_pool=self.endpoint_pool, mem_explorer=self.mem_explorer)

        mem_subset.add_res(new_tuple)
        return mem_subset

    def try_to_extend_subset(self,  subset : MemSubset, amount : int):
        """Try to extend subset memory by the specified amount
        ----------

        Parameters
        ----------
        subset : SubSet
            The targeted subset
        amount : int
            Resources requested

        Returns
        -------
        success : bool
            Return success status of operation
        """
        initial_tuple = subset.get_res()[0]
        
        bound_inf, bound_sup = initial_tuple
        new_tuple = (bound_inf, bound_sup+amount)
        
        success = self.__check_capacity_bound(bounds=new_tuple) 
        if not success: return False

        success = self.__check_overlap(new_tuple=new_tuple, initial_tuple=initial_tuple) 
        if not success: return False
        
        subset.remove_res(initial_tuple)
        subset.add_res(new_tuple)
        return True

    def __check_capacity_bound(self, bounds : tuple):
        """Check if specified extension (as tuple of bounds) verify host capacity
        ----------

        Parameters
        ----------
        bounds : tuple
            Bounds of memory

        Returns
        -------
        res : boolean
            True if host capacity handles extension. False otherwise.
        """
        host_capacity = self.memset.get_allowed()
        if bounds[0] < 0 : return False
        if bounds[1] > host_capacity: return False
        return True

    def __check_overlap(self, new_tuple : tuple, initial_tuple : tuple = None):
        """Check if specified tuple modification overlaps with others memsubset
        ----------

        Parameters
        ----------
        initial_tuple : int
            initial tuple
        new_tuple : int
            Tuple modified

        Returns
        -------
        res : boolean
            True if overlap, false otherwise.
        """
        for other_tuple in self.collection.get_res():
            if other_tuple == initial_tuple: continue
            print(other_tuple, new_tuple)
            overlap = max(0, min(new_tuple[1], other_tuple[1]) - max(new_tuple[0], other_tuple[0]))
            if overlap>0: return False
        return True

    def shrink_subset(self, subset : MemSubset = None):
        """Reduce subset capacity based on current allocation
        ----------

        Parameters
        ----------
        subset : Subset (opt)
            The subset to shrink(if not specified, all subset will be shrinked)
        """
        unused = subset.unused_resources_count()
        initial_tuple = subset.get_res()[0]
        subset.remove_res(initial_tuple)
        if unused < initial_tuple[1]: subset.add_res((initial_tuple[0], initial_tuple[1]-unused))
        super().shrink_subset(subset)

    def get_appropriate_id(self, vm : DomainEntity):
        """For a given VM, get its appropriate subset ID (corresponds to its premium policy)
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        id : int
            Its oversubscription ratio as subset ID
        """
        return 1 # Memory is out of scope of this paper

    def get_current_resources_usage(self):
        """Get usage of physical Memory resources

        Returns
        -------
        Usage : int
            Percentage [0:1]
        """
        return self.mem_explorer.get_usage_global()

    def get_request(self, vm : DomainEntity):
        """For a given VM, return its memory request
        ----------

        Parameters
        ----------
        vm : DomainEntity
            The VM to consider

        Returns
        -------
        mem : int
            Memory request of given VM
        """
        return vm.get_mem(as_kb=False) # in MB

    def get_res_name(self):
        """Get resource name managed by ManagerSubset
        ----------

        Return
        ----------
        res : str
            resource name
        """
        return 'mem'

    def __str__(self):
        return 'MemSubsetManager:\n' +  str(self.collection)

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
        req_attributes = ['connector', 'endpoint_pool', 'cpuset', 'memset']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        self.cpu_subset_manager = CpuSubsetManager(connector=self.connector, endpoint_pool=self.endpoint_pool, cpuset=self.cpuset, distance_max=50)
        self.mem_subset_manager = MemSubsetManager(connector=self.connector, endpoint_pool=self.endpoint_pool, memset=self.memset)
        self.vm_list = list()
        for vm in self.connector.get_vm_alive_as_entity(): 
            success = self.deploy(vm) # Treat pre-existing VM as deployment
            print('Deployement', vm.get_name(), success)
            self.vm_list.append(vm)

    def deploy(self, vm : DomainEntity):
        """Deploy a VM on subset managers
        ----------
        
        Parameters
        ----------
        vm : DomainEntity
            The VM to deploy

        Returns
        -------
        success : bool
            Return success status of operation
        """

        # For testing purposes only
        if 'alpinelinux3.14-2' in vm.get_name():
            setattr(vm, 'cpu_ratio', 2)
            print('changing oc', vm.get_cpu_ratio())

        mem_success = self.mem_subset_manager.deploy(vm)
        if not mem_success: return False
        cpu_success = self.cpu_subset_manager.deploy(vm)
        if not cpu_success:
            self.mem_subset_manager.remove(vm)
            return False
        return True

    def remove(self, vm : DomainEntity):
        """Remove a VM from subset managers
        ----------
        
        Parameters
        ----------
        vm : DomainEntity
            The VM to deploy

        Returns
        -------
        success : bool
            Return success status of operation
        """
        mem_success = self.mem_subset_manager.remove(vm)
        if not mem_success: return False
        cpu_success = self.cpu_subset_manager.remove(vm)
        if not cpu_success: raise ValueError('Invalid configuration encountered')
        return True

    def iterate(self, timestamp : int):
        # Manage monitoring
        self.cpu_subset_manager.update_monitoring(timestamp=timestamp)
        self.mem_subset_manager.update_monitoring(timestamp=timestamp)

        print(self.cpu_subset_manager)
        print(self.mem_subset_manager)

    def __str__(self):
        return str(self.cpu_subset_manager) + '\n' + str(self.mem_subset_manager) + '\n'