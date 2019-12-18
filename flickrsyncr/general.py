"""Common definitions."""
import logging
import sys


__all__ = ['CHECKSUM_TAG_PREFIX', 'SyncError', 'VERSION']


VERSION = '0.2.1'  # The canonical version definition.


# The tag naming is returned to users differently than it is set. When set, use "machine" mode.
CHECKSUM_TAG_PREFIX = 'checksum:md5='
CHECKSUM_TAG_PREFIX_NORMALIZED = 'checksummd5'


# Custom exception class used to terminate execution.
class SyncError(Exception):
    pass
