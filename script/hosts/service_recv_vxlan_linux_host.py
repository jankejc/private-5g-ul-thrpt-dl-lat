import time
from typing import Optional

from hosts.ntp_ip_node import NtpIpNode
from utils import print_info, print_success, print_error
from hosts.vxlan_linux_host import VxlanHost, VxlanLinuxHost


class ServiceRecvVxlanLinuxHost(VxlanLinuxHost):
    """I want only service receiver (Lenovo) to run tests."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run_vxlan_ping_test(self,
                            dest_host: VxlanHost,
                            ping_count: int,
                            ping_interval: float,
                            ntp: NtpIpNode,
                            packet_size: int = 0,
                            save_pcap: bool = True
                            ) -> bool:
        """If packet size = 0 it will be default from ping."""

        self.setup_log_subdirectory(self.log_dir, f"{packet_size}/ping_logs")
        if save_pcap:
            self.setup_log_subdirectory(self.log_dir, f"{packet_size}/pcap")

        filename = ntp.get_ntp_time()

        try:
            ping_log = f"{self.log_dir}/{packet_size}/ping_logs/{filename}.log"
            pcap_file = f"{self.log_dir}/{packet_size}/pcap/{filename}.pcap" if save_pcap else None

            print_info(
                f"Running Ping on {self.vxlan_ip} / {self.management_ip} "
                f"to {dest_host.vxlan_ip} / {dest_host.management_ip} with packet size {packet_size}, "
                f"count {ping_count}, interval {ping_interval}s...")

            # Running ping for 10 seconds before proper test to eliminate unstable pings at the beginning.
            pre_ping_command = f"ping -c 10 {dest_host.vxlan_ip}"
            self.execute_command(pre_ping_command)

            # Start capturing all traffic with tcpdump if enabled
            if save_pcap:
                tcpdump_command = f"tcpdump -i any -w {pcap_file} &"
                self.execute_command(tcpdump_command)

            if packet_size > 0:
                command = f"ping -s {packet_size} -c {ping_count} -i {ping_interval} {dest_host.vxlan_ip} > {ping_log} 2>&1"
            else:
                command = f"ping -c {ping_count} -i {ping_interval} {dest_host.vxlan_ip} > {ping_log} 2>&1"

            _, stderr, exit_status = self.execute_command(command)

            # Stop tcpdump after ping test if enabled
            if save_pcap:
                self.execute_command("pkill -f 'tcpdump -i any'")

            if exit_status == 0:
                msg = f"Ping Packet Size {packet_size} completed successfully."
                if save_pcap:
                    msg += f" Pcap saved as {pcap_file}."
                print_success(msg)
                return True
            else:
                print_error(f"Ping for Packet Size {packet_size} failed: {stderr}")
                return False
        except Exception as e:
            print_error(f"Exception during Ping for Packet Size {packet_size}: {e}")
            return False
