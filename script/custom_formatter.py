import sys
import logging
import re

# Custom formatter class that strips ANSI escape codes
class CustomFormatter(logging.Formatter):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

    def format(self, record):
        original = super(CustomFormatter, self).format(record)
        return self.ansi_escape.sub('', original)