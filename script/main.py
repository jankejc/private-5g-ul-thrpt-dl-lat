import logging
import time

from hosts.amarisoft_host import AmarisoftHost
from hosts.attenuator_host import AttenuatorHost
from hosts.ntp_ip_node import NtpIpNode
from hosts.service_recv_vxlan_linux_host import ServiceRecvVxlanLinuxHost
from hosts.vxlan_host import VxlanHost
from utils import print_success, print_error, print_info

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

AMARISOFT = {
    "username": "root",
    "password": "toor",
    "management_ip": "10.29.4.193",
    "log_dir": "/root/websockets",
    "five_g_ip": "192.168.2.1",
    "config_dir": "/root/enb/config",
    "service_name": "lte",
    "public_ip": None,
    "remote_api_port": 9001,
}

LENOVO = {
    "username": "lenovo",
    "password": "husarion",
    "management_ip": "10.29.4.197",
    "log_dir": "/home/lenovo/Documents/jk_article/tests/test_run",
    "vxlan_ip": "10.15.20.238",
    "public_ip": None,
}

ATTENUATOR = {
    "username": None,
    "password": None,
    "management_ip": "10.29.4.194",
    "public_ip": None,
}

LIDAR = {
    "management_ip": None,
    "username": None,
    "password": None,
    "vxlan_ip": "10.15.20.220",
    "public_ip": None,
}

NTP = {
    "public_ip": "153.19.250.123",
}

PING_COUNT_CONNECTION_CHECK = 10
PING_DURATION = 60  # seconds
PING_INTERVAL = 0.2
DEFAULT_PACKET_SIZE = 0
SAVE_PCAP = True
MAX_WAIT_TIME = 600  # 10 minutes max wait for UE connection
ATTENUATION_VALUES = [15, 20, 25]  # Modify as needed
CONFIG_FILES = [
    "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1.cfg",
    "pb-178-tdd-low-latency.cfg"
]


def wait_for_ue_connection(pinging_host, pinged_host, ping_count, ping_interval):
    print_info("Waiting for UE to connect...")
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT_TIME:
        if pinging_host.is_vxlan_ping(pinged_host, ping_count, ping_interval):
            print_success("UE successfully connected.")
            return True
        print_info("UE not connected yet. Retrying in 10 seconds...")
        time.sleep(5)

    print_error("UE did not connect after waiting.")
    return False


def main():
    attenuator = AttenuatorHost(
        username=ATTENUATOR["username"],
        password=ATTENUATOR["password"],
        management_ip=ATTENUATOR["management_ip"],
        public_ip=ATTENUATOR["public_ip"],
    )

    lidar = VxlanHost(
        management_ip=LIDAR["management_ip"],
        username=LIDAR["username"],
        password=LIDAR["password"],
        vxlan_ip=LIDAR["vxlan_ip"],
        public_ip=LIDAR["public_ip"],
    )

    amarisoft = AmarisoftHost(
        username=AMARISOFT["username"],
        password=AMARISOFT["password"],
        management_ip=AMARISOFT["management_ip"],
        log_dir=AMARISOFT["log_dir"],
        five_g_ip=AMARISOFT["five_g_ip"],
        config_dir=AMARISOFT["config_dir"],
        service_name=AMARISOFT["service_name"],
        public_ip=AMARISOFT["public_ip"],
        remote_api_port=AMARISOFT["remote_api_port"],
    )
    if not amarisoft.connect():
        print_error("Failed to connect to Amarisoft.")
        return

    lenovo = ServiceRecvVxlanLinuxHost(
        username=LENOVO["username"],
        password=LENOVO["password"],
        management_ip=LENOVO["management_ip"],
        log_dir=LENOVO["log_dir"],
        vxlan_ip=LENOVO["vxlan_ip"],
        public_ip=LENOVO["public_ip"],
    )
    if not lenovo.connect():
        print_error("Failed to connect to Lenovo / Husarion.")
        return

    ntp_server = NtpIpNode(public_ip=NTP["public_ip"])


    for config in CONFIG_FILES:
        print_info(f"Setting configuration: {config}")
        if not amarisoft.set_configuration(config):
            print_error(f"Failed to set {config}. Skipping...")
            continue

        for attn in ATTENUATION_VALUES:
            print_info(f"Setting attenuation to {attn} dB")
            if not attenuator.set_all_attenuations(attn):
                print_error(f"Failed to set attenuation {attn} dB. Skipping...")
                continue

            print_info("Restarting Amarisoft after setting attenuation...")
            if not amarisoft.restart_service():
                print_error("Failed to restart Amarisoft after attenuation change.")
                continue

            if not wait_for_ue_connection(lenovo,
                                          lidar,
                                          PING_COUNT_CONNECTION_CHECK,
                                          PING_INTERVAL
                                          ):
                print_error("UE did not connect. Stopping.")
                return

            print_info("Waiting for stable connection...")
            time.sleep(5)

            # todo: adjust
            print(amarisoft.get_stats(ntp_server))

            if not lenovo.run_vxlan_ping_test(lidar,
                                              PING_DURATION,
                                              PING_INTERVAL,
                                              ntp_server,
                                              DEFAULT_PACKET_SIZE,
                                              SAVE_PCAP,
                                              ):
                print_error("Ping test failed after attenuation change.")
                continue

    amarisoft.disconnect()
    lenovo.disconnect()
    print_success("Test sequence completed successfully.")

if __name__ == "__main__":
    main()

