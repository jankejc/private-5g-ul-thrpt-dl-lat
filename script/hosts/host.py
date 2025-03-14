from typing import Optional

from hosts.ip_node import IpNode


class Host(IpNode):
    def __init__(self,
                 username: Optional[str],
                 password: Optional[str],
                 management_ip: str,
                 **kwargs
                 ):
        super().__init__(**kwargs)
        self.username: Optional[str] = username
        self.password: Optional[str] = password
        self.management_ip: Optional[str] = management_ip
