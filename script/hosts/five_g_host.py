from typing import Optional

from hosts.linux_host import Host


class FiveGHost(Host):
    def __init__(self, five_g_ip: str, **kwargs):
        super().__init__(**kwargs)
        self.five_g_ip = five_g_ip
