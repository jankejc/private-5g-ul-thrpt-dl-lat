import time
import ntplib
import logging

NTP_SERVER = "153.19.250.123"

class NTPTime:
    @staticmethod
    def get_ntp_time():
        try:
            client = ntplib.NTPClient()
            response = client.request(NTP_SERVER, version=3)
            return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(response.tx_time))
        except Exception as e:
            logging.error(f"Failed to get NTP time: {e}")
            return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
