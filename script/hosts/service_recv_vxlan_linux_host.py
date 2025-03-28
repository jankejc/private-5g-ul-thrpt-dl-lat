import time

from utils import print_info, print_success, print_error
from hosts.vxlan_linux_host import VxlanHost, VxlanLinuxHost


class ServiceRecvVxlanLinuxHost(VxlanLinuxHost):
    """I want only service receiver (Lenovo) to run tests."""
    def __init__(self, vxlan_if: str, receiver_name: str, **kwargs):
        super().__init__(**kwargs)
        self.vxlan_if = vxlan_if
        self.receiver_name = receiver_name

    def run_vxlan_ping_test(self,
                            dest_host: VxlanHost,
                            ping_count: int,
                            dynamic_log_dir: str,
                            ping_size: int = 0,
                            save_pcap: bool = True,
                            ) -> bool:
        """If packet size = 0 it will be default from ping."""

        filename = time.strftime("%Y%m%d-%H%M%S", time.localtime())

        self.setup_log_directory(f"{dynamic_log_dir}/{ping_size}/ping_logs")
        if save_pcap:
            self.setup_log_directory(f"{dynamic_log_dir}/{ping_size}/pcap")

        try:
            ping_log = f"{dynamic_log_dir}/{ping_size}/ping_logs/{filename}.log"
            pcap_file = f"{dynamic_log_dir}/{ping_size}/pcap/{filename}.pcap" if save_pcap else None

            print_info(
                f"[{self.receiver_name}] Running Ping on {self.vxlan_ip} / {self.management_ip} "
                f"to {dest_host.vxlan_ip} / {dest_host.management_ip} with packet size {ping_size}, "
                f"count {ping_count}, interval {self.min_ping_interval}s...")

            # Running ping for 10 pings before proper test to eliminate unstable pings at the beginning.
            pre_ping_command = f"ping -c 10 {dest_host.vxlan_ip}"
            self.execute_command(pre_ping_command)

            # Start capturing all traffic with tcpdump if enabled
            if save_pcap:
                tcpdump_command = f"sudo tcpdump -ni {self.vxlan_if} -w {pcap_file} > /dev/null 2>&1 &"
                self.execute_command(tcpdump_command)

            if ping_size > 0:
                command = f"ping -s {ping_size} -c {ping_count} -i {self.min_ping_interval} {dest_host.vxlan_ip} > {ping_log} 2>&1"
            else:
                command = f"ping -c {ping_count} -i {self.min_ping_interval} {dest_host.vxlan_ip} > {ping_log} 2>&1"

            _, stderr, exit_status = self.execute_command(command)

            time.sleep(15)

            # Stop tcpdump after ping test if enabled
            # TODO check
            if save_pcap:
                self.execute_command(f"sudo pkill -SIGINT -f 'tcpdump -ni {self.vxlan_if}'")

            if exit_status == 0:
                msg = f"[{self.receiver_name}] Ping Packet Size {ping_size} completed successfully."
                if save_pcap:
                    msg += f" PCAP saved as {pcap_file}."
                print_success(msg)
                return True
            else:
                print_error(f"[{self.receiver_name}] Ping for Packet Size {ping_size} failed: {stderr}")
                return False
        except Exception as e:
            print_error(f"[{self.receiver_name}] Exception during Ping for Packet Size {ping_size}: {e}")
            return False
