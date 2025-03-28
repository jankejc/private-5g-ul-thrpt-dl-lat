import datetime
import logging
import threading
import time

from hosts.amarisoft_host import AmarisoftHost
from hosts.attenuator_host import AttenuatorHost
from hosts.ntp_ip_node import NtpIpNode
from hosts.service_recv_vxlan_linux_host import ServiceRecvVxlanLinuxHost
from hosts.vxlan_host import VxlanHost
from hosts.vxlan_linux_host import VxlanLinuxHost
from utils import print_success, print_error, print_info

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

AMARISOFT = {
    "username": "root",
    "password": "toor",
    "management_ip": "10.29.4.193",
    "log_dir": "/root/websockets/run_stats",
    "five_g_ip": "192.168.2.1",
    "config_dir": "/root/enb/config",
    "service_name": "lte",
    "public_ip": None,
    "remote_api_port": 9001,
    "min_ping_interval": None,
}

LENOVO = {
    "username": "lenovo",
    "password": "husarion",
    "management_ip": "10.29.4.197",
    "log_dir": "/home/lenovo/Documents/jk_article/tests/test_run",
    "vxlan_ip": "10.15.20.238",
    "public_ip": None,
    "min_ping_interval": 1,
    "vxlan_if": "enp92s0",
    "name": "LENOVO",
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

RPI = {
    "management_ip": "10.29.4.196",
    "username": "kti2",
    "password": "kti",
    "log_dir": "/home/kti2/JK_MAG/logs",
    "vxlan_ip": "10.15.20.184",
    "public_ip": None,
    "min_ping_interval": 0.2,
}

GET_TRACE_INTERVAL = 0.4 # By looking at created files Amari respond in about 400ms
PING_COUNT_CONNECTION_CHECK = 10
PING_DURATION = 60  # seconds
DEFAULT_LINUX_PING_PAYLOAD = 56
SAVE_PCAP = True
MAX_WAIT_TIME = 600  # 10 minutes max wait for UE connection
ATTENUATION_VALUES = [5] # can dangerous for setup
PACKET_SIZES = [16, 256, 512, 1024, 1436]
CONFIG_FILES = [
    "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1.cfg",
    "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1-better.cfg",
    # "pb-178-tdd-low-latency.cfg",
]


def wait_for_ue_connection(pinging_host: ServiceRecvVxlanLinuxHost,
                           pinged_host: VxlanHost,
                           ping_count: int,
                           ):
    print_info("Waiting for UE to connect...")
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT_TIME:
        if pinging_host.is_vxlan_ping(pinged_host, ping_count):
            print_success("UE successfully connected.")
            return True
        print_info("UE not connected yet. Retrying in 10 seconds...")
        time.sleep(5)

    print_error("UE did not connect after waiting.")
    return False


def get_time() -> str:
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d-%H%M%S")


def save_traces(amarisoft: AmarisoftHost, interval: float, dynamic_log_dir: str, stop_event: threading.Event):
    """
    Calls amarisoft.save_trace every 100ms until stop_event is set.
    """
    while not stop_event.is_set():
        amarisoft.save_trace(dynamic_log_dir)
        time.sleep(interval)


def start_saving_trace(amarisoft: AmarisoftHost, interval: float, dynamic_log_dir: str) -> (threading.Event, threading.Event):
    # Create an event to signal when the ping test is done.
    stop_event = threading.Event()

    # Start the trace saver thread.
    trace_thread = threading.Thread(
        target=save_traces,
        args=(amarisoft, interval, dynamic_log_dir, stop_event)
    )
    trace_thread.start()

    return stop_event, trace_thread


def stop_saving_trace(stop_event: threading.Event, trace_thread: threading.Thread):
    # When the ping test finishes, signal the trace saver thread to stop.
    stop_event.set()
    trace_thread.join()


def main():
    # lenovo will host test
    lenovo = ServiceRecvVxlanLinuxHost(
        username=LENOVO["username"],
        password=LENOVO["password"],
        management_ip=LENOVO["management_ip"],
        log_dir=LENOVO["log_dir"],
        vxlan_ip=LENOVO["vxlan_ip"],
        public_ip=LENOVO["public_ip"],
        min_ping_interval=LENOVO["min_ping_interval"],
        vxlan_if=LENOVO["vxlan_if"],
        receiver_name=LENOVO["name"],
    )
    if not lenovo.connect():
        print_error("Failed to connect to Lenovo / Husarion.")
        return

    dynamic_root_dir_filename = get_time()

    # todo: check on lenovo - fixed dirs
    # lenovo.setup_logging(dynamic_root_dir_filename)

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
        min_ping_interval=AMARISOFT["min_ping_interval"],
    )
    if not amarisoft.connect():
        print_error("Failed to connect to Amarisoft.")
        return

    ntp_server = NtpIpNode(public_ip=NTP["public_ip"])

    rpi = VxlanLinuxHost(
        username=RPI["username"],
        password=RPI["password"],
        management_ip=RPI["management_ip"],
        log_dir=RPI["log_dir"],
        vxlan_ip=RPI["vxlan_ip"],
        public_ip=RPI["public_ip"],
        min_ping_interval=RPI["min_ping_interval"],
    )

    print_info(f"Synchronizing Amarisoft and Lenovo")
    prev_ntp_lenovo = lenovo.ntp_on(ntp_server)
    prev_ntp_amari = amarisoft.ntp_on(ntp_server)

    # todo: change to lidar when it will finally work
    tested_node: VxlanHost = rpi

    for config in CONFIG_FILES:
        print_info(f"Setting configuration: {config}")
        if not amarisoft.set_configuration(config):
            print_error(f"Failed to set {config}. Skipping...")
            continue

        for attn in ATTENUATION_VALUES: 
            amarisoft_dynamic_log_dir = f"{amarisoft.log_dir}/{dynamic_root_dir_filename}/{config}/{attn}"
            lenovo_dynamic_log_dir = f"{lenovo.log_dir}/{dynamic_root_dir_filename}/{config}/{attn}"

            print_info(f"Setting attenuation to {attn} dB")
            if not attenuator.set_all_attenuations(attn):
                print_error(f"Failed to set attenuation {attn} dB. Skipping...")
                continue


            # print_info("Restarting Amarisoft after setting attenuation...")
            # if not amarisoft.restart_service():
            #     print_error("Failed to restart Amarisoft after attenuation change.")
            #     continue

            # if not wait_for_ue_connection(lenovo,
            #                               tested_node,
            #                               PING_COUNT_CONNECTION_CHECK,
            #                               ):
            #     print_error("UE did not connect. Stopping.")
            #     return

            print_info("Waiting for stable connection...")
            # time.sleep(5)

            # TODO check packeting
            for packet_size in PACKET_SIZES:
                print_info(f"Checking packet size: {packet_size}B")
                print_info(f"Starting getting trace each {GET_TRACE_INTERVAL}s...")
                stop_event, trace_thread = start_saving_trace(amarisoft, GET_TRACE_INTERVAL, amarisoft_dynamic_log_dir)

                # if not lenovo.run_vxlan_ping_test(tested_node,
                #                                   PING_DURATION,
                #                                   filename,
                #                                   lenovo_dynamic_log_dir,
                #                                   packet_size,
                #                                   SAVE_PCAP
                #                                   ):
                #     print_error("Ping test failed after attenuation change.")
                #     continue

                print_info(f"Stopping getting trace")
                stop_saving_trace(stop_event, trace_thread)

    print_info(f"Reverse synchronisation on Amarisoft and Lenovo")
    lenovo.ntp_off(prev_ntp_lenovo)
    amarisoft.ntp_off(prev_ntp_amari)

    print_info(f"Disconnecting from Amarisoft and Lenovo")
    amarisoft.disconnect()
    lenovo.disconnect()
    print_success("Test sequence completed successfully.")

if __name__ == "__main__":
    main()

