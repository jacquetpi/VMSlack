import sys, getopt
from dotenv import load_dotenv
from schedulerlocal.node.numaexplorer import NumaExplorer
from schedulerlocal.node.servercpuset import ServerCpuSet
from schedulerlocal.domain.libvirtconnector import LibvirtConnector
from schedulerlocal.schedulerlocal import SchedulerLocal

def print_usage():
    print('todo')

if __name__ == '__main__':

    short_options = "hd:l:"
    long_options = ["help", "debug=", "load="]

    cpuset = None
    debug_level = 0
    try:
        arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print(str(err))
        print_usage()
    for current_argument, current_value in arguments:
        if current_argument in ('-h', '--help'):
            print_usage()
        elif current_argument in('-l', '--load'):
            cpuset = ServerCpuSet().load_from_json(current_value).build_distances()
        elif current_argument in('-d', '--debug'):
            debug_level = int(current_value)

    ###########################################
    # First, build node CPU set
    ###########################################
    if cpuset is None:
        explorer = NumaExplorer()
        cpuset = explorer.build_cpuset()
    if debug_level>0: cpuset.dump_as_json('debug/cpuset_local.json')

    ###########################################
    # Second, initiate local libvirt connection
    ###########################################
    libvirt_connector = LibvirtConnector(url='qemu:///system')

    ###########################################
    # Third, launch scheduling facilities
    ###########################################
    scheduler_local = SchedulerLocal(tick=2, debug_level=debug_level)
    try:
        scheduler_local.run()
    except KeyboardInterrupt:
        print("Program interrupted")
        del scheduler_local
        sys.exit(0)