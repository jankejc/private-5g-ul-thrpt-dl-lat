from hosts.five_g_host import FiveGHost
from hosts.linux_host import LinuxHost


class LinuxFiveGHost(LinuxHost, FiveGHost):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
