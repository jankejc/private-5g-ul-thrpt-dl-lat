from typing import Optional, Dict
from requests import codes
from hosts.linux_host import Host
from utils import print_error, print_success

import requests


class AttenuatorHost(Host):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def read_attenuation(self, channel: int = 1) -> Optional[str]:
        if not self.is_valid_channel(channel):
            return None
        try:
            url = f'http://{self.management_ip}/rdstate.cgi?&chnl={channel}'
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            attenuation_level = self.extract_value(response.text, "attn")
            if attenuation_level:
                print_success(f"Channel {channel}: Attenuation Level = {attenuation_level} dB")
                return attenuation_level
            else:
                raise ValueError("Attenuation value not found in response.")
        except requests.RequestException as e:
            print_error(f"HTTP error while reading attenuation: {e}")
            return None
        except ValueError as e:
            print_error(f"Parsing error while reading attenuation: {e}")
            return None

    def set_attenuation(self, channel: int = 1, attenuation: float = 15.0) -> bool:
        if not self.is_valid_channel(channel) or not self.is_valid_attenuation(attenuation):
            return False
        try:
            url = (f'http://{self.management_ip}/setup.cgi?&chnl={channel}'
                   f'&UIchnl={channel}&freq=3950&lattnsz=1.0&tattnsz=0.1&attn={attenuation}')
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            if response.status_code == codes.ok:
                print_success(f"Channel {channel}: Attenuation set to {attenuation} dB")
                return True
            else:
                raise ValueError(f"Unexpected response code: {response.status_code}")
        except requests.RequestException as e:
            print_error(f"HTTP error while setting attenuation: {e}")
            return False
        except ValueError as e:
            print_error(f"Response error while setting attenuation: {e}")
            return False

    def set_all_attenuations(self, attenuation: float) -> bool:
        success = True
        for channel in range(1, 5):
            if not self.set_attenuation(channel, attenuation):
                success = False
        return success

    def read_all_attenuations(self) -> Dict[int, Optional[str]]:
        attenuations = {}
        for channel in range(1, 5):
            attn = self.read_attenuation(channel)
            attenuations[channel] = attn
        return attenuations


    def extract_value(self, response_text: str, key: str) -> Optional[str]:
        for item in response_text.split(';'):
            if item.startswith(f"{key}="):
                return item.split('=')[1]
        return None


    def is_valid_channel(self, channel: int) -> bool:
        if 1 <= channel <= 4:
            return True
        print_error(f"Invalid channel: {channel}. Valid range is 1-4.")
        return False


    def is_valid_attenuation(self, attenuation: float) -> bool:
        if 0.0 <= attenuation <= 120.0:
            return True

        print_error(f"Invalid attenuation: {attenuation}. Valid range is 0.0-120.0 dB.")
        return False
