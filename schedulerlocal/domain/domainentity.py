class DomainEntity:

    def __init__(self, **kwargs):
        req_attributes = []
        for req_attribute in req_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', req_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])