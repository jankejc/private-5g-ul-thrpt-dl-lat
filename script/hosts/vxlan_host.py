from typing import Optional

from hosts.host import Host


class VxlanHost(Host):
    def __init__(self, vxlan_ip: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self.vxlan_ip = vxlan_ip