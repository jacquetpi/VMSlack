from collections import defaultdict
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv
import os, json
from schedulerlocal.subset.subset import Subset
from schedulerlocal.node.cpuexplorer import CpuExplorer
from schedulerlocal.node.memoryexplorer import MemoryExplorer

class Endpoint(object):
    """
    An Endpoint is a class charged to store or retrieve subset data 
    Abstract class
    ...

    Public Methods
    -------
    todo()
        todo
    """

    def load(self, timestamp : int, subset : Subset):
        """Return available resources. Must be reimplemented
        ----------
        """
        raise NotImplementedError()

    def store(self):
        """Return available resources. Must be reimplemented
        ----------
        """
        raise NotImplementedError()

class EndpointLive(Endpoint):
    """
    A live endpoint load data from the live system. It cannot store data
    ...

    Public Methods
    -------
    todo()
        todo
    """
        
    def load(self, timestamp : int, subset : Subset):
        usage = subset.get_current_usage() # Use subset specific connector and/or explorer
        return usage

class EndpointInfluxDB(Endpoint):
    """
    An InfluxDB endpoint store and load data from InfluxDB
    ...

    Public Methods
    -------
    todo()
        todo
    """

    def __init__(self, **kwargs):
        load_dotenv()
        self.url    =  os.getenv('INFLUXDB_URL')
        self.token  =  os.getenv('INFLUXDB_TOKEN')
        self.org    =  os.getenv('INFLUXDB_ORG')
        self.bucket =  os.getenv('INFLUXDB_BUCKET')
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.query_api = self.client.query_api()
        except Exception as ex:
            print('An exception occured while trying to connect to InfluxDB, double check your parameters:')
            print('url:', self.url, 'org:', self.org, 'token: [hidden]')
            print('Full stack trace is:\n')
            raise ex

    def load(self, begin_epoch : int, end_epoch : int):
        """TODO
        ----------
        """
        query = ' from(bucket:"' + self.bucket + '")\
        |> range(start: ' + str(begin_epoch) + ', stop: ' + str(end_epoch) + ')\
        |> filter(fn: (r) => r["_measurement"] == "domain")\
        |> filter(fn: (r) => r["url"] == "' + self.model_node_name + '")'

        result = self.query_api.query(org=self.org, query=query)
        domains_data = defaultdict(lambda: defaultdict(list))

        for table in result:
            for record in table.records:
                domain_name = record.__getitem__('domain')
                timestamp = (record.get_time()).timestamp()
                if timestamp not in domains_data[domain_name]["time"]:
                    domains_data[domain_name]["time"].append(timestamp)
                domains_data[domain_name][record.get_field()].append(record.get_value())
        return domains_data

    def store():
        """TODO
        ----------
        """
        return 'todo'

class EndpointCSV(Endpoint):
    """
    A CSV endpoint store and load data from a CSV file
    ...

    Public Methods
    -------
    todo()
        todo
    """

    def __init__(self, **kwargs):
        req_attributes = ['file']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        
        with open(self.input_file, 'r') as f: 
            self.input_data = json.load(f)
        self.output_data = dict()

class EndpointJson(Endpoint):
    """
    A Json endpoint store and load data from a json file
    ...

    Public Methods
    -------
    todo()
        todo
    """

    def __init__(self, **kwargs):
        req_attributes = ['file']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        
        with open(self.input_file, 'r') as f: 
            self.input_data = json.load(f)
        self.output_data = dict()

    def load(self, begin_epoch : int, end_epoch : int):
        """TODO
        ----------
        """
        return self.input_data

    def store(self, data):
        """TODO
        ----------
        """
        self.output_data = data

    def __del__(self):
        """Before destroying object, dump written data
        ----------
        """
        print("JsonEndpoint: dumping data to", self.output_file)
        with open(self.output_file, 'w') as f: 
            f.write(json.dumps(self.output_data))