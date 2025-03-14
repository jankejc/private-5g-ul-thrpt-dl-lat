import os
import posixpath
import stat
from typing import Optional, Tuple
import paramiko

from hosts.host import Host
from utils import print_info, print_success, print_error


class LinuxHost(Host):
    def __init__(self, log_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.log_dir = log_dir
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


    def setup_log_directory(self) -> bool:
        try:
            command = f"rm -rf {self.log_dir_ping} && mkdir -p {self.log_dir_ping}"
            _, stderr, exit_status = self.execute_command(command)
            if exit_status == 0:
                print_info(f"Log directory for ping ensured: {self.log_dir_ping}")
                return True
            else:
                print_error(f"Error creating log directory {self.log_dir_ping}: {stderr}")
                return False

        except Exception as e:
            print_error(f"Exception while creating log directory {self.log_dir_iperf} or {self.log_dir_ping}: {e}")
            return False


    def setup_log_subdirectory(self, directory_path: str, subdirectory_name: str) -> bool:
        try:
            command = f"mkdir -p {directory_path}/{subdirectory_name}"
            _, stderr, exit_status = self.execute_command(command)
            if exit_status == 0:
                print_info(f"Log subdirectory ensured: {directory_path}/{subdirectory_name}")
            else:
                print_error(f"Error creating log subdirectory {directory_path}/{subdirectory_name}: {stderr}")
                return False

        except Exception as e:
            print_error(f"Exception while creating log subdirectory {directory_path + subdirectory_name}: {e}")
            return False
        

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
        
