from typing import Optional


class IpNode:
    def __init__(self, public_ip: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self.public_ip: Optional[str] = public_ip