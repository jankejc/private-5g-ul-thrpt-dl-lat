from typing import Optional

from hosts.linux_host import LinuxHost
from hosts.vxlan_host import VxlanHost
from utils import print_info, print_error

import re


class VxlanLinuxHost(LinuxHost, VxlanHost):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def is_vxlan_ping(self,
                      dest_host: "VxlanHost",
                      count: int = 1,
                      ) -> bool:
        try:
            command = f"ping -c {count} -i {self.min_ping_interval} {dest_host.vxlan_ip}"
            stdout, stderr, exit_status = self.execute_command(command)

            if len(stderr) == 0:
                print(stdout)
                match = re.search(r'(\d+) packets transmitted, (\d+) received', stdout)
                received_packets = int(match.group(2))
                if received_packets == count:
                    print_info(f"Ping to {dest_host.vxlan_ip} successful.")
                    return True
                else:
                    print_info(f"Ping to {dest_host.vxlan_ip} unsuccessful.")
                    return False

            else:
                print_error(f"Error while pinging {dest_host.vxlan_ip}.")
                print_error(stdout)
                print_error(stderr)
                print_error(exit_status)

                return False

        except Exception as e:
            print_error(f"Exception during ping to {dest_host.vxlan_ip}: {e}")
            return False

    def is_mikrotik_ping(self,
                         dest_host: "VxlanHost",
                         count: int = 1,
                         ) -> bool:
        try:
            command = f"/ping {dest_host.vxlan_ip} count={count} interval={self.min_ping_interval}"
            stdout, stderr, exit_status = self.execute_command(command)

            if len(stderr) == 0:
                print(stdout)
                match = re.search(r'sent=(\d+)\s+received=(\d+)', stdout)
                received_packets = int(match.group(2))
                if received_packets > 0:
                    print_info(f"Ping to {dest_host.vxlan_ip} successful.")
                    return True
                else:
                    print_info(f"Ping to {dest_host.vxlan_ip} unsuccessful.")
                    return False

            else:
                print_error(f"Error while pinging {dest_host.vxlan_ip}.")
                print_error(stdout)
                print_error(stderr)
                print_error(exit_status)

                return False

        except Exception as e:
            print_error(f"Exception during ping to {dest_host.vxlan_ip}: {e}")
            return False

    def turn_off_interface(self, interface: str) -> bool:
        try:
            command = f"/interface disable [find name=\"{interface}\"]"
            stdout, stderr, exit_status = self.execute_command(command)

            if len(stderr) == 0:
                print_info(f"[MIKROTIK] Interface {interface} turned OFF.")
                return True

            else:
                print_error(f"Error while turning OFF the interface {interface}.")
                print_error(stdout)
                print_error(stderr)
                print_error(exit_status)

                return False

        except Exception as e:
            print_error(f"Exception during turning OFF the interface {interface}: {e}")
            return False

    def turn_on_interface(self, interface: bool) -> bool:
        try:
            command = f"/interface enable [find name=\"{interface}\"]"
            stdout, stderr, exit_status = self.execute_command(command)

            if len(stderr) == 0:
                print_info(f"[MIKROTIK] Interface {interface} turned ON.")
                return True

            else:
                print_error(f"Error while turning ON the interface {interface}.")
                print_error(stdout)
                print_error(stderr)
                print_error(exit_status)

                return False

        except Exception as e:
            print_error(f"Exception during turning ON the interface {interface}: {e}")
            return False