import logging
import sys


__all__ = ['setupStatus', 'updateStatus']
status_logger = None


def setupStatus(logger=None):
    # if enable:
    #     global stream
    #     stream = sys.stdout
    """Sets up a logger for the status output. Goes to stdout."""
    global status_logger
    if logger:
        status_logger = logger
    else:
        formatter = logging.Formatter('%(message)s')
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)

        status_logger = logging.getLogger('flickrsyncr_status')
        status_logger.setLevel(logging.INFO)
        status_logger.addHandler(handler)


def updateStatus(msg):
    if status_logger is not None:
        status_logger.info(msg)
