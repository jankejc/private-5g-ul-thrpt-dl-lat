import json
import websocket

from typing import Optional
from hosts.linux_five_g_core_host import LinuxFiveGCoreHost
from hosts.ntp_ip_node import NtpIpNode
from utils import print_info


class AmarisoftHost(LinuxFiveGCoreHost):
    def __init__(self,
                 remote_api_port: Optional[int],
                 **kwargs
                 ):
        super().__init__(**kwargs)
        self.remote_api_port = remote_api_port

    # todo: add ntp stamping
    def save_stats(self, filename: str, amarisoft_dynamic_log_dir: str):
        print_info(f"Connecting via WebSocket at {self.management_ip}:{self.remote_api_port}")
        ws = websocket.create_connection(f"ws://{self.management_ip}:{self.remote_api_port}", origin="Test")
        ws.send('{"message":"stats"}'.encode('utf-8'))

        result = ""
        while True:
            response = ws.recv()
            if response:
                message = json.loads(response)
                result += json.dumps(message, indent=2, ensure_ascii=False) + "\n"
                if message.get("message") != "ready":
                    break

        ws.close()

        self.execute_command(f"{response} > {amarisoft_dynamic_log_dir}/{filename}")


