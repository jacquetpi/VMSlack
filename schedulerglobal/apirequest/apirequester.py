import requests, json

class ApiRequester(object):
    """
    The API requester manage calls to localschedulers instance
    ...

    Attributes
    ----------
    url_list : list
        List of node urls

    Public Methods
    -------
    deploy_on()
        Deploy a VM on node
    remove_from()
        Remove a VM from node
    info_of()
        Return info of a node
    """
    
    def __init__(self, **kwargs):
        req_attributes = []
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])


    def deploy_on(self, host_url : str, name : str, cpu : str, memory : str, ratio : str, disk : str):
        """Deploy a VM on specified host based on requested specification
        ----------

        Parameters
        ----------
        host_url : str
            Host targeted for deployment
        name : str
            VM name as str
        cpu : str
            Number of vcpu as str
        memory : str
            Memory (gb) as str
        ratio :  str
            Premium policy to apply
        disk :  str
            Disk location

        Returns
        -------
        response : str
            Return result of operation as str
        """
        constructed_url = host_url + '/deploy?name=' + name + '&cpu=' + cpu + '&memory=' + memory +\
             '&oc=' + ratio + '&qcow2=' + disk
        response = requests.get(constructed_url)
        return response.json()

    def remove_from(self,  host_url : str, name : str):
        """Remove VM from specified node
        ----------

        Parameters
        ----------
        host_url : str
            Host targeted
        vm : str
            Name of VM to be removed

        Returns
        -------
        response : str
            Return result of operation as str
        """
        constructed_url = host_url + '/remove?name=' + name
        response = requests.get(constructed_url)
        return response.json()

    def status_of(self, host_url : str):
        """Return the state of requested host
        ----------

        Parameters
        ----------
        host_url : str
            Host targeted

        Returns
        -------
        state : str
            Cluster related info as str
        """
        constructed_url = host_url + '/status'
        response = requests.get(constructed_url)
        return response.json()