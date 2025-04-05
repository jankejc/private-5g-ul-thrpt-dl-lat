import os
import posixpath
import stat
import sys

import paramiko
import logging

from typing import Optional, Tuple
from hosts.host import Host
from utils import print_info, print_success, print_error

from custom_formatter import CustomFormatter
from hosts.ntp_ip_node import NtpIpNode
from stream_to_logger import StreamToLogger


class LinuxHost(Host):
    def __init__(self, log_dir: Optional[str], min_ping_interval: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self.log_dir = log_dir
        self.min_ping_interval = min_ping_interval
        self.ssh_client: Optional[paramiko.SSHClient] = None

    def connect(self) -> bool:
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(hostname=self.management_ip, username=self.username, password=self.password)
            print_success(f"Connected to SSH server {self.management_ip} successfully.")
            return True
        except Exception as e:
            print_error(f"Connection error to {self.management_ip}: {e}")
            return False

    def disconnect(self) -> None:
        if self.ssh_client:
            self.ssh_client.close()
            print_info(f"Disconnected from {self.management_ip}.")

    def execute_command(self, command: str) -> Tuple[str, str, int]:
        if not self.ssh_client:
            raise ConnectionError("SSH client not connected.")

        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()

        return stdout.read().decode(), stderr.read().decode(), exit_status

    def setup_log_directory(self, directory_path: str) -> bool:
        try:
            command = f"mkdir -p {directory_path}"
            _, stderr, exit_status = self.execute_command(command)
            if exit_status == 0:
                print_info(f"Log directory ensured: {directory_path}")
            else:
                print_error(f"Error creating log directory {directory_path}: {stderr}")
                return False

        except Exception as e:
            print_error(f"Exception while creating log directory {directory_path}: {e}")
            return False

    def setup_logging(self, results_dir: str):
        self.setup_log_directory(results_dir)

        # Configure the root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Disable propagation to avoid duplicates in the root logger
        logger.propagate = False

        # Create file handler
        file_handler = logging.FileHandler(f"{results_dir}/run_logs.log", mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(CustomFormatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Redirect stdout and stderr to the logger
        sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
        sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)

    def download_logs(self, sftp, remote_dir, local_dir):
        # Recursively download all files and subdirectories in a remote directory to a local directory.
        try:
            # Ensure the local directory exists
            os.makedirs(local_dir, exist_ok=True)

            # Get all items in the directory
            for item in sftp.listdir_attr(remote_dir):
                remote_path = posixpath.join(remote_dir, item.filename)
                local_path = os.path.join(local_dir, item.filename)

                # Check if it's a directory
                if stat.S_ISDIR(item.st_mode):
                    # Recursive call to download directory
                    print_info(f"Entering directory {remote_path}")
                    self.download_logs(sftp, remote_path, local_path)
                else:
                    # Download files
                    print_info(f"Downloading {remote_path} to {local_path}")
                    sftp.get(remote_path, local_path)
                    print_success(f"Downloaded {item.filename} to {local_path}")
        except Exception as e:
            print_error(f"Error downloading logs from {self.management_ip}: {e}")
            return False

    def download_all_logs(self, local_dir: str) -> bool:
        try:
            sftp = self.ssh_client.open_sftp()
            self.download_logs(sftp, self.log_dir_iperf, local_dir)
            self.download_logs(sftp, self.log_dir_ping, local_dir)
            sftp.close()
            return True
        except Exception as e:
            print_error(f"Error downloading all logs from {self.management_ip}: {e}")
            return False

    def ntp_on(self, ntp_server: NtpIpNode) -> Optional[str]:
        """
        Sets the NTP server to ntp_server.public_ip.

        - If an active NTP line exists with a different IP, replace it and return that IP.
        - If an active NTP line already equals ntp_server.public_ip, do nothing.
        - If only a commented NTP line exists, replace it with an active line and return None.
        """
        """
        If you "sudo timedatectl set-ntp false" then "systemctl status systemd-timesyncd" will be disabled.
        Then if you "sudo timedatectl set-ntp true" then "systemctl status systemd-timesyncd" will be enabled.
        Finally if you "systemctl restart systemd-timesyncd" after "sudo timedatectl set-ntp false" it will also enable the service.
        It's connected to each other.
        """

        # Get the current NTP line (either active or commented).
        get_ntp_cmd = "sudo grep -E '^[#]?NTP=' /etc/systemd/timesyncd.conf"
        result = self.execute_command(get_ntp_cmd)[0].strip()

        if not result:
            # If no NTP line exists, insert it at the top.
            insert_cmd = f"sudo sed -i '1s/^/NTP={ntp_server.public_ip}\\n/' /etc/systemd/timesyncd.conf"
            self.execute_command(insert_cmd)
            self.execute_command("sudo systemctl restart systemd-timesyncd")
            return None

        current_line = result.strip()
        # Remove any leading '#' and extra whitespace.
        line_no_comment = current_line.lstrip('#').strip()
        if not line_no_comment.startswith("NTP="):
            # Fallback: replace the entire line with our setting.
            new_line = f"NTP={ntp_server.public_ip}"
            replace_cmd = f"sudo sed -i 's/.*/{new_line}/' /etc/systemd/timesyncd.conf"
            self.execute_command(replace_cmd)
            self.execute_command("sudo systemctl restart systemd-timesyncd")
            return None

        # Extract the current IP value.
        current_ip = line_no_comment.split("=", 1)[1].strip()
        if current_ip == ntp_server.public_ip:
            return None
        else:
            new_line = f"NTP={ntp_server.public_ip}"
            # Replace any line starting with (optional '#') NTP= with our new setting.
            replace_cmd = f"sudo sed -i 's/^[#]*NTP=.*/{new_line}/' /etc/systemd/timesyncd.conf"
            self.execute_command(replace_cmd)
            self.execute_command("sudo systemctl restart systemd-timesyncd")
            # If the original line was active (not commented), return the previous IP; if it was commented, return None.
            return current_ip if current_line.startswith("NTP=") else None

    def ntp_off(self, prev_ntp_ip: str):
        """
        Restores the previous NTP server if provided.
        If no previous NTP was set, simply comments out the current one.
        """
        if prev_ntp_ip:
            restore_ntp_cmd = f"sudo sed -i 's|^NTP=.*|NTP={prev_ntp_ip}|' /etc/systemd/timesyncd.conf"
            self.execute_command(restore_ntp_cmd)
        else:
            # Comment out current NTP setting if no previous NTP
            comment_out_ntp_cmd = "sudo sed -i 's/^NTP=/#NTP=/' /etc/systemd/timesyncd.conf"
            self.execute_command(comment_out_ntp_cmd)

        # Restart systemd-timesyncd
        restart_ntp_cmd = "sudo systemctl stop systemd-timesyncd"
        self.execute_command(restart_ntp_cmd)




