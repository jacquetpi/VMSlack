from collections import defaultdict
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv
import os, json

class HistoryManager(object):
    """
    An History manager is a class charged to retrieve history data 
    Abstract class
    ...

    Public Methods
    -------
    todo()
        todo
    """

    def get_data(self):
        """Return available resources. Must be reimplemented
        ----------
        """
        raise NotImplementedError()

    def put_data(self):
        """Return available resources. Must be reimplemented
        ----------
        """
        raise NotImplementedError()

class InfluxDBHistoryManager(HistoryManager):

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

    def get_data(self, begin_epoch : int, end_epoch : int):
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

    def put_data():
        """TODO
        ----------
        """
        return 'todo'

class OneShotJSONBHistoryManager(HistoryManager):
    """
    An History manager is a class charged to retrieve history data 
    Abstract class
    ...

    Public Methods
    -------
    todo()
        todo
    """

    def __init__(self, **kwargs):
        req_attributes = ['input_file', 'output_file']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        
        with open(self.input_file, 'r') as f: 
            self.input_data = json.load(f)
        self.output_data = dict()

    def get_data(self, begin_epoch : int, end_epoch : int):
        """TODO
        ----------
        """
        return self.input_data

    def put_data(self, data):
        """TODO
        ----------
        """
        self.output_data = data

    def __del__(self):
        """Before destroying object, dump written data
        ----------
        """
        print("OneShotJSONBHistoryManager: dumping data to", self.output_file)
        with open(self.output_file, 'w') as f: 
            f.write(json.dumps(self.output_data))