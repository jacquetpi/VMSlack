from json import JSONEncoder
from schedulerlocal.node.memoryset import ServerMemorySet
from schedulerlocal.node.cpuset import ServerCpuSet

class ServerCpuSetEncoder(JSONEncoder):
    """
    Class to specify on to convert ServerCpuSet to JSON
    ...

    Public MethodsServerCpuSet
        json conversion
    """

    def default(self, o):
        """Implements Conversion strategy
        ----------

        Parameters
        ----------
        o : object
            object to convert
        """
        if type(o) is not ServerCpuSet:
            return
        as_dict = dict(o.__dict__)
        as_dict['cpu_list'] = [element.__dict__ for element in o.__dict__['cpu_list']]
        return as_dict

class ServerMemorySetEncoder(JSONEncoder):
    """
    Class to specify on to convert MemoryCpuSet to JSON
    ...

    Public MethodsServerCpuSet
        json conversion
    """

    def default(self, o):
        """Implements Conversion strategy
        ----------

        Parameters
        ----------
        o : object
            object to convert
        """
        if type(o) is not ServerMemorySet:
            return
        as_dict = dict(o.__dict__)
        return as_dict

class GlobalEncoder(JSONEncoder):
    """
    Class to specify on to convert ServerCpuSet to JSON
    ...

    Public MethodsServerCpuSet
        json conversion
    """

    def default(self, o, *args, **kwargs):
        """Implements Conversion strategy
        ----------

        Parameters
        ----------
        o : object
            object to convert
        """
        if type(o) is ServerCpuSet:
            return ServerCpuSetEncoder(*args, **kwargs).default(o)
        elif type(o) is ServerMemorySet:
            return ServerMemorySetEncoder(*args, **kwargs).default(o)
        elif type(o) is dict:
            return dict(o.__dict__)
        else:
            raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')