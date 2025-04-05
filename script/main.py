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
    "management_ip": "10.29.4.197",
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
    "management_ip": "10.29.4.196",
    "log_dir": "/home/lenovo/Documents/jk_article/tests/test_run",
    "vxlan_ip": "192.168.123.1",
    # additional network just to enable ping -> variable should be ping_ip instead of vxlan_ip
    "public_ip": None,
    "min_ping_interval": "0,2",
    "vxlan_if": "enp92s0",
    "name": "LENOVO",
}

ATTENUATOR = {
    "username": None,
    "password": None,
    "management_ip": "10.29.4.194",
    "public_ip": None,
}

MIKROTIK_5G = {
    "management_ip": "10.29.4.121",
    "username": "admin",
    "password": "kti",
    "vxlan_ip": "192.168.123.2",
    # additional network just to enable ping -> variable should be ping_ip instead of vxlan_ip
    "public_ip": None,
    "log_dir": None,
    "min_ping_interval": "100ms"
}

MIKROTIK_EDGE = {
    "management_ip": "10.29.4.129",
    "username": "admin",
    "password": "kti",
    "vxlan_ip": None,
    "public_ip": None,
    "log_dir": None,
    "min_ping_interval": "100ms"
}

NTP = {
    "public_ip": "153.19.250.123",
}

""" In case there would be linux host instead of LiDAR """
# RPI = {
#     "management_ip": "10.29.4.196",
#     "username": "kti2",
#     "password": "kti",
#     "log_dir": "/home/kti2/JK_MAG/logs",
#     "vxlan_ip": "10.15.20.184",
#     "public_ip": None,
#     "min_ping_interval": 0.2,
# }

# FLAGS
TEST_PING = False
TEST_THROUGHPUT = True
SAVE_PCAP = True  # I don't see scenario where it should be False. It needs to be True when TEST_THROUGHPUT is True.

LIDAR_OUT_INTERFACE = "ether23"
GET_TRACE_INTERVAL = 1  # By looking at created files Amari respond in about 400ms
PING_COUNT_CONNECTION_CHECK = 100
PING_COUNT_UPLINK = 100
TEST_SEC_DURATION = 20
PING_TEST_COUNT = int(
    TEST_SEC_DURATION / float(LENOVO["min_ping_interval"].replace(",", ".")))  # test duration / lenovo interval
PING_REPETITION = 30
DEFAULT_LINUX_PING_PAYLOAD = 56
MAX_WAIT_TIME = 1200  # 20 minutes max wait for UE connection, 10 minutes too low when max lidar
ATTENUATION_VALUES = [0]  # potentially dangerous for setup
# PACKET_SIZES = [16, 256, 512, 1024, 1436]
PACKET_SIZES = [56]
CONFIG_FILES = [
    # "pb-178-tdd-low-latency-20.cfg",
    # "pb-178-tdd-low-latency.cfg",
    # "pb-178-tdd-low-latency-no-rx-to-tx-lat.cfg",
    # "pb-178-tdd-low-latency-prach-160.cfg",
    # "pb-178-tdd-low-latency-rx-to-tx-lat-1.cfg",
    # "pb-178-tdd-low-latency-rx-to-tx-lat-2.cfg",
    # "pb-178-tdd-low-latency-rx-to-tx-lat-4.cfg",
    # "pb-178-tdd-low-latency-sr-per-1.cfg",
    # "pb-178-ul-highTp-autoCSI-noTRS-20.cfg",
    # "pb-178-ul-highTp-autoCSI-noTRS.cfg",
    # # "pb-178-ul-highTp-autoCSI-noTRS-prach-128-sr-per-1.cfg",
    # "pb-178-ul-highTp-autoCSI-noTRS-prach-128.cfg",
    # "pb-178-ul-highTp-autoCSI-noTRS-sr-per-1.cfg",
    # "pb-178-ul-highTp-autoCSI-TRSonSSB-20.cfg",
    # "pb-178-ul-highTp-autoCSI-TRSonSSB.cfg",
    # # "pb-178-ul-highTp-autoCSI-TRSonSSB-prach-128-sr-per-1.cfg",
    # "pb-178-ul-highTp-autoCSI-TRSonSSB-prach-128.cfg",
    "pb-178-ul-highTp-autoCSI-TRSonSSB-rx-to-tx-lat-2.cfg",
    "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1.cfg",
    "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1-uss.cfg",
    "pb-178-ul-highTp-defCSI-20.cfg",
    "pb-178-ul-highTp-defCSI.cfg",
    "pb-178-ul-highTp-defCSI-no-trs.cfg",
    "pb-178-ul-highTp-defCSI-prach-128.cfg",
    "pb-178-ul-highTp-defCSI-rx-to-tx-lat-2.cfg",
    "pb-178-ul-highTp-defCSI-rx-to-tx-lat-4.cfg",
    "pb-178-ul-highTp-defCSI-sr-per-1.cfg"
]


def wait_for_ue_connection(pinging_host: ServiceRecvVxlanLinuxHost,
                           pinged_host: VxlanLinuxHost,
                           amarisoft: AmarisoftHost,
                           ping_count: int,
                           ):
    print_info("Waiting for UE to connect...")
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT_TIME:
        if pinging_host.is_vxlan_ping(pinged_host, ping_count):
            print_success("UE successfully connected.")
            return True

    print_error(f"UE did not connect after waiting {MAX_WAIT_TIME / 60} minutes.")
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


def start_saving_trace(amarisoft: AmarisoftHost, interval: float, dynamic_log_dir: str) -> (
threading.Event, threading.Event):  # type: ignore
    # Create an event to signal when the ping test is done.
    stop_event = threading.Event()

    # Start the trace saver thread.
    trace_thread = threading.Thread(
        target=save_traces,
        args=(amarisoft, interval, dynamic_log_dir, stop_event)
    )
    trace_thread.start()

    return stop_event, trace_thread


def start_uplink_ping(mikrotik: VxlanLinuxHost, lenovo: VxlanLinuxHost) -> (
threading.Event, threading.Event):  # type: ignore
    # Create an event to signal when the ping should be done.
    stop_event = threading.Event()

    # Start the trace saver thread.
    uplink_ping_thread = threading.Thread(
        target=uplink_ping,
        args=(mikrotik, lenovo, stop_event)
    )
    uplink_ping_thread.start()

    return stop_event, uplink_ping_thread


def uplink_ping(mikrotik: VxlanLinuxHost, lenovo: VxlanLinuxHost, stop_event: threading.Event):
    """
    Calls pinged_host.is_mikrotik_ping 100ms until stop_event is set.
    """
    while not stop_event.is_set():
        # Sometimes VxLAN is dying and we need something like heartbeat from UE.
        if mikrotik.is_mikrotik_ping(lenovo, PING_COUNT_UPLINK):
            print_success("Ping Mikrotik 5G -> Lenovo successful! Waiting for downlink ping...")


def stop_thread(stop_event: threading.Event, trace_thread: threading.Thread):
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

    attenuator = AttenuatorHost(
        username=ATTENUATOR["username"],
        password=ATTENUATOR["password"],
        management_ip=ATTENUATOR["management_ip"],
        public_ip=ATTENUATOR["public_ip"],
    )

    mikrotik = VxlanLinuxHost(
        management_ip=MIKROTIK_5G["management_ip"],
        username=MIKROTIK_5G["username"],
        password=MIKROTIK_5G["password"],
        vxlan_ip=MIKROTIK_5G["vxlan_ip"],
        public_ip=MIKROTIK_5G["public_ip"],
        log_dir=MIKROTIK_5G["log_dir"],
        min_ping_interval=MIKROTIK_5G["min_ping_interval"]
    )
    if not mikrotik.connect():
        print_error("Failed to connect to Mikrotik 5G.")
        return

    mikrotik_edge = VxlanLinuxHost(
        management_ip=MIKROTIK_EDGE["management_ip"],
        username=MIKROTIK_EDGE["username"],
        password=MIKROTIK_EDGE["password"],
        vxlan_ip=MIKROTIK_EDGE["vxlan_ip"],
        public_ip=MIKROTIK_EDGE["public_ip"],
        log_dir=MIKROTIK_EDGE["log_dir"],
        min_ping_interval=MIKROTIK_EDGE["min_ping_interval"]
    )
    if not mikrotik_edge.connect():
        print_error("Failed to connect to Mikrotik EDGE.")
        return

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

    # rpi = VxlanLinuxHost(
    #     username=RPI["username"],
    #     password=RPI["password"],
    #     management_ip=RPI["management_ip"],
    #     log_dir=RPI["log_dir"],
    #     vxlan_ip=RPI["vxlan_ip"],
    #     public_ip=RPI["public_ip"],
    #     min_ping_interval=RPI["min_ping_interval"],
    # )

    # We use manually set chrony.
    # print_info(f"Synchronizing Amarisoft and Lenovo")
    # prev_ntp_lenovo = lenovo.ntp_on(ntp_server)
    # prev_ntp_amari = amarisoft.ntp_on(ntp_server)

    dynamic_root_dir_filename = get_time()
    lenovo.setup_logging(f"{lenovo.log_dir}/{dynamic_root_dir_filename}")

    tested_node: VxlanLinuxHost = mikrotik

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

            # Lidar traffic destabilize initial connection, so we turn it off for a moment
            print_info("Turning off Mikrotik LiDAR interface...")
            mikrotik_edge.turn_off_interface(LIDAR_OUT_INTERFACE)

            print_info("Restarting Amarisoft after setting attenuation...")
            if not amarisoft.restart_service():
                print_error("Failed to restart Amarisoft after attenuation change.")
                continue

            print_info("Waiting 15 seconds before redirect for Amarisoft to be ready...")
            time.sleep(15)
            print_info("Redirecting traffic on Amarisoft to enable PING...")
            amarisoft.redirect_ping()

            stop_uplink_ping_event, uplink_ping_thread = start_uplink_ping(mikrotik, lenovo)

            if not wait_for_ue_connection(lenovo,
                                          tested_node,
                                          amarisoft,
                                          PING_COUNT_CONNECTION_CHECK,
                                          ):
                print_error("UE did not connect. Stopping.")
                stop_thread(stop_uplink_ping_event, uplink_ping_thread)
                return

            print_info(f"Stopping uplink ping...")
            stop_thread(stop_uplink_ping_event, uplink_ping_thread)

            if TEST_THROUGHPUT:
                print_info("Turning on Mikrotik LiDAR interface...")
                mikrotik_edge.turn_on_interface(LIDAR_OUT_INTERFACE)

            print_info("Waiting for stable connection...")
            time.sleep(5)

            for packet_size in PACKET_SIZES:
                print_info(f"Checking packet size: {packet_size}B")

                for ping_repeat_num in range(1, PING_REPETITION + 1):
                    if TEST_PING and not TEST_THROUGHPUT:
                        print_info(
                            f"Starting TEST with PING repeat: {ping_repeat_num} with packet size: {packet_size} for {attn} dB in {config}")
                    elif TEST_THROUGHPUT and not TEST_PING:
                        print_info(
                            f"Starting TEST with THROUHGPUT repeat: {ping_repeat_num} with packet size: {packet_size} for {attn} dB in {config}")
                    elif TEST_PING and TEST_THROUGHPUT:
                        print_info(
                            f"Starting TEST with PING and THROUGHPUT repeat: {ping_repeat_num} with packet size: {packet_size} for {attn} dB in {config}")
                    else:
                        print_error("No test selected. Skipping ping / throughput test.")
                        return

                    # On amarisoft ping repeat will be mentioned in directory name becuase there will be multiple files per ping repeat.
                    amarisoft_dynamic_log_dir = f"{amarisoft.log_dir}/{dynamic_root_dir_filename}/{config}/attn_{attn}/{packet_size}B/rep_{ping_repeat_num}"
                    # On lenovo ping repeat will be in filename because there will be one file for each run.
                    lenovo_dynamic_log_dir = f"{lenovo.log_dir}/{dynamic_root_dir_filename}/{config}/attn_{attn}"

                    print_info(f"Starting getting trace each {GET_TRACE_INTERVAL}s...")
                    stop_saving_trace_event, trace_thread = start_saving_trace(amarisoft, GET_TRACE_INTERVAL,
                                                                               amarisoft_dynamic_log_dir)

                    if not lenovo.run_vxlan_test(tested_node,
                                                 TEST_PING,
                                                 TEST_THROUGHPUT,
                                                 PING_TEST_COUNT,
                                                 TEST_SEC_DURATION,
                                                 lenovo_dynamic_log_dir,
                                                 ping_repeat_num,
                                                 packet_size,
                                                 SAVE_PCAP
                                                 ):
                        print_error("Ping test failed after attenuation change.")
                        stop_thread(stop_saving_trace_event, trace_thread)
                        continue

                    print_info(f"Stopping getting trace")
                    # When the ping test finishes, signal the trace saver thread to stop.
                    stop_thread(stop_saving_trace_event, trace_thread)

    # We use manually set chrony.
    # print_info(f"Reverse synchronisation on Amarisoft and Lenovo")
    # lenovo.ntp_off(prev_ntp_lenovo)
    # amarisoft.ntp_off(prev_ntp_amari)

    print_info(f"Disconnecting from Amarisoft and Lenovo")
    amarisoft.disconnect()
    lenovo.disconnect()
    mikrotik.disconnect()
    print_success("Script didn't crashed.")


if __name__ == "__main__":
    main()