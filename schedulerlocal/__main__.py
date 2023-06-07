import os, sys, getopt, json
from dotenv import load_dotenv
from schedulerlocal.node.cpuexplorer import CpuExplorer
from schedulerlocal.node.cpuset import ServerCpuSet
from schedulerlocal.node.memoryexplorer import MemoryExplorer
from schedulerlocal.node.memoryset import ServerMemorySet
from schedulerlocal.node.jsonencoder import GlobalEncoder
from schedulerlocal.domain.libvirtconnector import LibvirtConnector
from schedulerlocal.schedulerlocal import SchedulerLocal
from schedulerlocal.hist.historymanager import HistoryManager, InfluxDBHistoryManager

def print_usage():
    print('todo')

if __name__ == '__main__':

    short_options = "hd:t:"
    long_options = ["help", "debug=", "topology="]

    cpuset = None
    memset = None
    debug_level = 0
    try:
        arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print(str(err))
        print_usage()
    for current_argument, current_value in arguments:
        if current_argument in ('-h', '--help'):
            print_usage()
        elif current_argument in('-t', '--topology'):
            with open(current_value, 'r') as f:
                json_topology = f.read()
            cpuset = ServerCpuSet().load_from_json(json_topology).build_distances()
            memset = ServerMemorySet().load_from_json(json_topology)
            print('test', memset.get_allowed())
        elif current_argument in('-d', '--debug'):
            debug_level = int(current_value)

    ###########################################
    # First, build node topology
    ###########################################
    if (cpuset is None) or (memset is None):
        cpuset = CpuExplorer().build_cpuset()
        memset = MemoryExplorer().build_memoryset()
        if debug_level>0:
            topology = {'cpuset': cpuset, 'memset': memset}
            with open('debug/topology_local.json', 'w') as f: 
                f.write(json.dumps(topology, cls=GlobalEncoder))

    ###########################################
    # Second, initiate local libvirt connection
    ###########################################
    libvirt_connector = LibvirtConnector(url='qemu:///system')

    ###########################################
    # Third, load history manager
    ###########################################
    history_manager = InfluxDBHistoryManager()

    ###########################################
    # Finally, launch scheduling facilities
    ###########################################
    scheduler_local = SchedulerLocal(cpuset=cpuset,\
                                    memset=memset,\
                                    connector=libvirt_connector,\
                                    tick=2,\
                                    debug_level=debug_level)
    try:
        scheduler_local.run()
    except KeyboardInterrupt:
        print("Program interrupted")
        del scheduler_local
        sys.exit(0)