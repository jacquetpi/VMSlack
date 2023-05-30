import sys, getopt, os, libvirt, json
from dotenv import load_dotenv

STATE_ENDPOINT = ""
LIBVIRT_NODES = dict()

def read_endpoint():
    return 'todo'

def display_status():
    return 'todo'

def deploy_vm_on_host(host: str, name : str, cpu : int, memory : int):
    try:
        conn = libvirt.open(LIBVIRT_NODES[host])
        return ''
    except libvirt.libvirtError as e:
        print(repr(e), file=sys.stderr)
        sys.exit(-1)
        
def deploy_vm(name : str, cpu : int, memory : int, ratio : float):
    for hostname, host_status in status.items():
        status = read_endpoint()
        deploy_vm_on_host(hostname, name, cpu, memory)
        return 'todo'

    print("No host found")

def print_usage():
    print("python3 name [--help] [--list=''] [--deploy=name,cpu,mem,ratio")

def convert_args_to_values(self, request_as_str):
    config = current_value.split(',')
    try:
        name = config[0]
        cpu = int(config[1])
        memory = int(config[2])
        ratio = int(config[3])
    except Exception:
        print_usage()
        sys.exit(-1)
    return name, cpu, memory, ratio

if __name__ == '__main__':

    short_options = "hld:"
    long_options = ["help", "list","deploy="]
 
    try:
        arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print (str(err)) # Output error, and return with an error code
        sys.exit(2)

    load_dotenv()
    STATE_ENDPOINT = os.getenv('STATE_ENDPOINT')
    LIBVIRT_NODES = json.loads(os.getenv('LIBVIRT_NODES'))

    for current_argument, current_value in arguments:
        if current_argument in ("-l", "--list"):
            display_status()
        elif current_argument in ("-d", "--deploy"):
            name, cpu, memory, ratio = convert_args_to_values(current_value)
            deploy_vm(name, cpu, memory, ratio)
        else:
            print_usage()