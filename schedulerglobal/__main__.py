import os, getopt, sys
from dotenv import load_dotenv
from schedulerglobal.schedulerglobal import SchedulerGlobal

SCHEDULERLOCAL_LIST = ''

def print_usage():
    print('python3 -m schedulerglobal name [--help] [--list=url1,url2]')
    print("If no url list is specified, the environment variable SCHEDULERLOCAL_LIST will be used")

if __name__ == '__main__':

    short_options = 'hl:'
    long_options = ['help', 'list=']
 
    try:
        arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print (str(err)) # Output error, and return with an error code
        sys.exit(2)

    load_dotenv()
    SCHEDULERLOCAL_LIST = os.getenv('SCHEDULERLOCAL_LIST')

    for current_argument, current_value in arguments:
        if current_argument in ("-l", "--list"):
            SCHEDULERLOCAL_LIST = current_value
        elif current_argument in ("-h", "--help"):
            print_usage()
            sys.exit(0)
        else:
            print_usage()
            sys.exit(-1)
    
    global_scheduler = SchedulerGlobal(url_list=SCHEDULERLOCAL_LIST.split(','),\
            api_url='127.0.0.1', api_port='8100',\
            delay=15)
    global_scheduler.run()