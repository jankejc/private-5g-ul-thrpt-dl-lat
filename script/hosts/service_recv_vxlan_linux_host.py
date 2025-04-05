import time

from utils import print_info, print_success, print_error
from hosts.vxlan_linux_host import VxlanHost, VxlanLinuxHost


class ServiceRecvVxlanLinuxHost(VxlanLinuxHost):
    """I want only service receiver (Lenovo) to run tests."""

    def __init__(self, vxlan_if: str, receiver_name: str, **kwargs):
        super().__init__(**kwargs)
        self.vxlan_if = vxlan_if
        self.receiver_name = receiver_name

    def run_vxlan_test(self,
                       dest_host: VxlanHost,
                       test_ping: bool,
                       test_throughput: bool,
                       ping_count: int,
                       test_duration: int,
                       dynamic_log_dir: str,
                       ping_repeat_num: int = 0,
                       ping_size: int = 0,
                       save_pcap: bool = True,
                       ) -> bool:
        """If packet size = 0 it will be default from ping."""

        filename = time.strftime("%Y%m%d-%H%M%S", time.localtime())

        if test_ping:
            self.setup_log_directory(f"{dynamic_log_dir}/{ping_size}B/ping_logs")

        if save_pcap:
            self.setup_log_directory(f"{dynamic_log_dir}/{ping_size}B/pcap")
        elif save_pcap == False and test_throughput == True:
            print_info("PCAP saving disabled, cannot calculate throughput.")
            return False

        try:
            ping_log = f"{dynamic_log_dir}/{ping_size}B/ping_logs/ping_{filename}_rep_{ping_repeat_num}.log"
            pcap_file = f"{dynamic_log_dir}/{ping_size}B/pcap/pcap_{filename}_rep_{ping_repeat_num}.pcap" if save_pcap else None

            # Otherwise these a lot pings can be lost under lidar traffic.
            if test_ping and test_throughput == False:
                # Running ping for 10 pings before proper test to eliminate unstable pings at the beginning.
                print_info("Running preping to assure connection.")
                pre_ping_command = f"ping -c 10 {dest_host.vxlan_ip} -i {self.min_ping_interval}"
                stdout, stderr, exit_status = self.execute_command(pre_ping_command)
                print(stdout)

            # Start capturing all traffic with tcpdump if enabled
            if save_pcap:
                tcpdump_command = f"sudo tcpdump -ni {self.vxlan_if} -w {pcap_file} > /dev/null 2>&1 &"
                self.execute_command(tcpdump_command)
                print_info(f"Started tcpdump on {self.vxlan_if} and saving to {pcap_file}")
                print_info("Heating tcpdump up for 5 seconds...")
                time.sleep(5)

            if test_ping:
                print_info(
                    f"[{self.receiver_name}] Running Ping on {self.vxlan_ip} / {self.management_ip} "
                    f"to {dest_host.vxlan_ip} / {dest_host.management_ip} with packet size {ping_size}, "
                    f"count {ping_count}, interval {self.min_ping_interval}s...")
                if ping_size > 0:
                    command = f"ping -s {ping_size} -c {ping_count} -i {self.min_ping_interval} {dest_host.vxlan_ip} > {ping_log} 2>&1"
                else:
                    command = f"ping -c {ping_count} -i {self.min_ping_interval} {dest_host.vxlan_ip} > {ping_log} 2>&1"

                stdout, stderr, exit_status = self.execute_command(command)

            elif test_throughput:
                print_info(
                    f"[{self.receiver_name}] Running only {test_duration} seconds of TCPDUMP to calculate throughput...")
                time.sleep(test_duration)

            else:
                print_info("No test selected. Skipping ping / throughput test.")
                return False

            # Stop tcpdump after ping test if enabled
            if save_pcap:
                print_info("Slowing tcpdump down for 5 seconds...")
                time.sleep(5)
                self.execute_command(f"sudo pkill -SIGINT -f 'tcpdump -ni {self.vxlan_if}'")

            if test_ping:
                if exit_status == 0:
                    print(stdout)
                    msg = f"[{self.receiver_name}] Ping Packet Size {ping_size} completed successfully."
                    if save_pcap:
                        msg += f" PCAP saved as {pcap_file}."
                    print_success(msg)
                    return True
                else:
                    print(stderr)
                    print_error(f"[{self.receiver_name}] Ping for Packet Size {ping_size} failed: {stderr}")
                    return False

            elif test_throughput:
                print_success(f"PCAP saved as {pcap_file}")
                return True

            else:
                print_info("No test selected. Skipping ping / throughput test.")
                return False

        except Exception as e:
            print_error(f"[{self.receiver_name}] Exception during Ping / Throughput test: {e}")
            return False
