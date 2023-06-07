import re
from schedulerlocal.node.memoryset import ServerMemorySet

class MemoryExplorer:
    """
    A class used to retrieve Memory Information
    ...

    Public Methods
    -------
    build_memoryset():
       Build a MemorySet object from linux filesystem data
    """

    def __init__(self, **kwargs):
        self.fs_meminfo = '/proc/meminfo'
        self.private_mb = kwargs['private_mb'] if 'private_mb' in kwargs else 0

    def build_memoryset(self):
        with open(self.fs_meminfo, 'r') as f:
            meminfo = f.read()
        total_found = re.search('^MemTotal:\s+(\d+)', meminfo)
        if not total_found: raise ValueError('Error while parsing', self.fs_meminfo)
        total_kb = int(total_found.groups()[0])
        total_mb = int(total_kb/1024)
        allowed_mb = total_mb - self.private_mb
        return ServerMemorySet(total=total_mb, allowed_mb=allowed_mb)