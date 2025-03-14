from typing import Optional

from hosts.linux_five_g_host import LinuxFiveGHost
from utils import print_success, print_error, print_info

import time


class LinuxFiveGCoreHost(LinuxFiveGHost):
    """I assume that all the 5G Cores are running linux."""
    def __init__(self,
                 service_name: str,
                 config_dir: str,
                 **kwargs
                 ):
        super().__init__(**kwargs)
        self.service_name = service_name
        self.config_dir = config_dir

    def set_configuration(self, config_file: str) -> bool:
        try:
            command = f"ln -sf {config_file} enb.cfg"
            stdin, stdout, stderr = self.ssh_client.exec_command(f"cd {self.config_dir} && {command}")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                print_success(f"Configuration set to {config_file}.")
                return True
            else:
                error_output = stderr.read().decode().strip()
                print_error(f"Failed to set configuration to {config_file}: {error_output}")
                return False
        except Exception as e:
            print_error(f"Exception while setting configuration {config_file}: {e}")
            return False

    def restart_service(self, timeout: int = 30) -> bool:
        try:
            print_info(f"Restarting service '{self.service_name}'...")
            command = f"systemctl restart {self.service_name}"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            stdout.channel.recv_exit_status()
            error_output = stderr.read().decode().strip()

            start_time = time.time()
            service_started = False

            print_info(f"Waiting for service '{self.service_name}' to start...")

            while time.time() - start_time < timeout:
                status = self.check_service_status()
                if status:
                    service_started = True
                    break
                time.sleep(1)

            if service_started:
                print_success(f"Service '{self.service_name}' restarted and is running.")
                return True
            else:
                if error_output:
                    print_error(f"Error restarting service '{self.service_name}': {error_output}")
                else:
                    print_error(f"Service '{self.service_name}' failed to start after {timeout} seconds.")
                return False
        except Exception as e:
            print_error(f"Error restarting service '{self.service_name}': {e}")
            return False

    def check_service_status(self, service_name: str = None) -> bool:
        if service_name is None:
            service_name = self.service_name
        try:
            command = f"systemctl is-active {service_name}"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            status = stdout.read().decode().strip()
            return status == 'active'
        except Exception as e:
            print_error(f"Error checking status of service '{service_name}': {e}")
            return False

    def apply_configuration(self, config_file: str) -> bool:
        if self.set_configuration(config_file):
            return self.restart_service()
        return False
