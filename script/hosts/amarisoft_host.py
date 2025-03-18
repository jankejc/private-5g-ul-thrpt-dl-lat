import json
from datetime import datetime

import websocket

from typing import Optional
from hosts.linux_five_g_core_host import LinuxFiveGCoreHost
from utils import print_info


class AmarisoftHost(LinuxFiveGCoreHost):
    def __init__(self,
                 remote_api_port: Optional[int],
                 **kwargs
                 ):
        super().__init__(**kwargs)
        self.remote_api_port = remote_api_port


    def save_trace(self, amarisoft_dynamic_log_dir: str):
        now = datetime.now()
        filename = now.strftime("%H%M%S") + f"-{int(now.microsecond / 1000):03d}"

        print_info(f"[AMARISOFT] Using Remote API via WebSocket at 127.0.0.1:{self.remote_api_port}")
        ws = websocket.create_connection(f"ws://{self.management_ip}:{self.remote_api_port}", origin="Test")
        ws.send('{"message":"ue_get", "stats":true}'.encode('utf-8'))

        result = ""
        while True:
            response = ws.recv()
            if response:
                message = json.loads(response)
                result += json.dumps(message, indent=2, ensure_ascii=False) + "\n"
                if message.get("message") != "ready":
                    break

        ws.close()

        self.execute_command(f"mkdir -p {amarisoft_dynamic_log_dir} && echo \"{result}\" > {amarisoft_dynamic_log_dir}/{filename} 2>&1")
