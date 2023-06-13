class EndpointPool(object):
    """
    An EndpointPool is a class composed of a loading endpoint and a saving endpoint
    ...

    Public Methods
    -------
    load()
        Return data from the loader, while also storing to the saver if it is defined
    loadOnly()
        Return data from the loader
    """

    def __init__(self, **kwargs):
        req_attributes = ['loader','saver']
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])

    def load(self, **kwargs):
        """Return data from the loader, while also storing to the saver if it is defined
        ----------

        Parameters
        ----------
        res : object
            The resource to add

        Return
        ----------
        data : dict
            Data as dict
        """
        data = self.loadOnly(**kwargs)
        if self.saver != None:
            self.saver.store()
        return data

    def loadOnly(self, **kwargs):
        """Return data from the loader
        ----------

        Parameters
        ----------
        res : object
            The resource to add

        Return
        ----------
        data : dict
            Data as dict
        """
        return self.loader.load(timestamp=kwargs['timestamp'], subset=kwargs['subset'])