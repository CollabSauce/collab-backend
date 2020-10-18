""" Custom loggers, filters, and formatters """
import json
import logging
from django.conf import settings


BLACKLIST_KEYS = ['password', 'password1', 'password2', 'new_password1', 'new_password2']


class CloudwatchLoggingFilter(logging.Filter):
    """ Filter which injects context for env on record
    """

    def filter(self, record):
        record.env = settings.ENVIRONMENT
        return True


class RequestLoggingFilter(logging.Filter):
    """ Filter out any 'password' data
    """

    def filter(self, record):
        try:
            if record.msg.startswith("b\'") and record.msg.endswith("\'"):
                msg = json.loads(record.msg[2:][:-1])
                for key in BLACKLIST_KEYS:
                    if key in msg:
                        msg[key] = 'REDACTED'
                record.msg = json.dumps(msg)
        except:
            pass
        return True
