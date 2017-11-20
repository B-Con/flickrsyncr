from flickrsyncr.general import CHECKSUM_TAG_PREFIX
from flickrsyncr.general import SyncError
from flickrsyncr.general import VERSION
from flickrsyncr.settings import Settings
from flickrsyncr.sync import sync


__doc__ = """FlickrSyncr provides logic for transfering files between a local
directory and a Flickr album.

* flickrsyncr.Settings is a class for specifying sync settings.
* flickrsyncr.sync accepts a Settings object and performs the syncing logic.
* flickrsyncr.SyncError is the generic error exception raised.

ex: Force the Flickr album contents to match local dir based only on file name.
flickrsyncr.sync(flickrsyncr.Settings('albumname', '/my/dir', push=True, sync=True))

ex: Force the Flickr album contents to match local dir based on file name and checksum.
flickrsyncr.sync(flickrsyncr.Settings('albumname', '/my/dir', push=True, sync=True, checksum=True))

ex: Add local files into a Flickr album.
flickrsyncr.sync(flickrsyncr.Settings('albumname', '/my/dir', push=True))

ex: Repeatedly upload locally changed files to the Flickr album.
flickrsyncr.sync(flickrsyncr.Settings('albumname', '/my/dir', push=True, sync=True, checksum=True))
# ...make edits...
flickrsyncr.sync(flickrsyncr.Settings('albumname', '/my/dir', push=True, sync=True, checksum=True))
# only modified files were uploaded

ex: Check what content would change if you were to add a Flickr album to a local dir.
flickrsyncr.sync(flickrsyncr.Settings('albumname', '/my/dir', pull=True, dryrun=True))
"""

__all__ = [
    'CHECKSUM_TAG_PREFIX',
    'SyncError',
    'Settings',
    'sync',
]
__author__ = 'Brad Conte'
__version__ = VERSION


if __name__ == '__main__':
    pass
