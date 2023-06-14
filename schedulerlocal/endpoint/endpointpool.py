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

    def load_subset(self, timestamp, subset):
        """Return subset data from the loader, while also storing to the saver if it is defined
        ----------

        Parameters
        ----------
        timestamp : int 
            timestamp requested
        subset : Subset
            Subset Object

        Return
        ----------
        data : dict
            Data as dict
        """
        data = self.load_subset_only(timestamp, subset)
        if self.saver != None:
            self.saver.store(data)
        return data

    def load_subset_only(self, timestamp, subset):
        """Return subset data from the loader
        ----------

        Parameters
        ----------
        timestamp : int 
            timestamp requested
        SubsetManager : Subset
            SubsetManager Object

        Return
        ----------
        data : dict
            Data as dict
        """
        return self.loader.load_subset(timestamp, subset)

    def load_global(self, timestamp, subset_manager):
        """Return global data from the loader, while also storing to the saver if it is defined
        ----------

        Parameters
        ----------
        timestamp : int 
            timestamp requested
        subset_manager : SubsetManager
            SubsetManager Object

        Return
        ----------
        data : dict
            Data as dict
        """
        data = self.load_global_only(timestamp, subset_manager)
        if self.saver != None:
            self.saver.store(data)
        return data

    def load_global_only(self, timestamp, subset_manager):
        """Return subset data from the loader
        ----------

        Parameters
        ----------
        timestamp : int 
            timestamp requested
        subset_manager : SubsetManager
            SubsetManager Object

        Return
        ----------
        data : dict
            Data as dict
        """
        return self.loader.load_global(timestamp, subset_manager)
