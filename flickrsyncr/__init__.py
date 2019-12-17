"""flickrsyncr package initialization."""

# Each module defines what it exports via __all__.
from .config import Config, loadConfigStore
from .flickrwrapper import getFlickrAPI
from .general import CHECKSUM_TAG_PREFIX, SyncError, VERSION
from .syncer import sync
from .status import setupStatus, updateStatus
from .__main__ import cli


__doc__ = """FlickrSyncr provides logic for transfering and merging files
between a local directory and a Flickr album.

* flickrsyncr.Config - a class for specifying configuration settings.
* flickrsyncr.sync - a function that to perform sync logic per config.
* flickrsyncr.SyncError - the exception raised on fatal errors.

ex: Force the Flickr album contents to match local dir based only on file name.
flickrsyncr.sync(flickrsyncr.Config('albumname', '/my/dir', push=True, sync=True))

ex: Force the Flickr album contents to match local dir based on file name and checksum.
flickrsyncr.sync(flickrsyncr.Config('albumname', '/my/dir', push=True, sync=True, checksum=True))

ex: Add local files to a Flickr album, modifying none of the existing album content.
flickrsyncr.sync(flickrsyncr.Config('albumname', '/my/dir', push=True))

ex: Upload locally changed files to the Flickr album.
flickrsyncr.sync(flickrsyncr.Config('albumname', '/my/dir', push=True, sync=True, checksum=True))
# ...make edits...
flickrsyncr.sync(flickrsyncr.Config('albumname', '/my/dir', push=True, sync=True, checksum=True))
# only modified files were uploaded ^

ex: Check what content would change if you were to add a Flickr album to a local dir.
flickrsyncr.sync(flickrsyncr.Config('albumname', '/my/dir', pull=True, dryrun=True))
"""

__author__ = 'Brad Conte'
