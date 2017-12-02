import logging


# Application version. The canonical source.
VERSION = '0.1.4'

# The tag naming is returned to users differently than it is set. When set, use "machine" mode.
CHECKSUM_TAG_PREFIX = 'checksum:md5='
CHECKSUM_TAG_PREFIX_NORMALIZED = 'checksummd5'

# Init the logger.
logger = logging.getLogger('flickrsyncr')
logger.setLevel(logging.NOTSET)


# Custom exception class used to terminate execution.
class SyncError(Exception):
    pass
