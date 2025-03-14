from utils import print_error
import ntplib
from hosts.ip_node import IpNode

import time

class NtpIpNode(IpNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_ntp_time(self):
        try:
            client = ntplib.NTPClient()
            response = client.request(self.public_ip, version=3)
            return time.strftime("%Y%m%d-%H%M%S", time.gmtime(response.tx_time))
        except Exception as e:
            print_error(f"Failed to get NTP time: {e}")
            return time.strftime("%Y%m%d-%H%M%S")
