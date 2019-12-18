#!/usr/bin/env python3

import argparse
import logging
import sys

import flickrapi
from .config import Config
from .config import loadConfigStore
from .flickrwrapper import getFlickrAPI
from .general import CHECKSUM_TAG_PREFIX
from .general import SyncError
from .general import VERSION
from .status import setupStatus
from .status import updateStatus
from .syncer import sync


def getCmdlineArgs():
    """Defines cmd-line arguments, parses them, and returns an object with each supplied arg name
    as a property.
    """
    parser = argparse.ArgumentParser(prog='flickrsyncr',
            description='Synchronize photos between a folder and a Flickr album.')

    parser.add_argument('--album', required=True, type=str,
            help='Name of the Flickr album. If there are multiple albums with the same name, ' +
            'the first one (per ordering in the user\'s account) will be used. If no album ' +
            'has this name during a --push, it will be created.')

    parser.add_argument('--path', required=True, type=str,
            help='Local path to use in the sync process. It must exist.')

    parser.add_argument('--api_key', default='', required=False, type=str,
            help='Flickr API Key associated with the account. Can alternatively be provided ' +
            'via the config file.')

    parser.add_argument('--api_secret', default='', required=False, type=str,
            help='Flickr API Secret associated with the account. Can alternatively be provided ' +
            'via the config file.')

    parser.add_argument('--checksum', action='store_true',
            help='Use checksums comparing local and Flickr content. Stores the checksum on ' +
            'a photo tag with prefix "' + CHECKSUM_TAG_PREFIX + '"". Allows ' +
            'file edits to be detected and synced. Without this only the filename and photo\'s ' +
            'title are used to compare files. Checksums are calculated at upload time, they ' +
            'are not updated if the photo is manually edited.')

    parser.add_argument('--config_dir', default='', type=str,
            help='Directory with the config file (with api_key and api_secret) and OAuth store.')

    parser.add_argument('--config_profile', default='', type=str,
            help='Profile name inside the config file to use.')

    parser.add_argument('--dryrun', action='store_true',
            help='Make no file or photo changes. Output & logs show what would have happened. ' +
            'Still obtains and stores OAuth credentials.')

    parser.add_argument('--loglevel', action='store', choices=['NOTSET', 'DEBUG', 'INFO',
            'WARNING', 'ERROR'], default='INFO',
            help='Verbosity for log output to --logfile. NOTSET produces no logs.')

    parser.add_argument('--logfile', action='store', type=str,
            help='File to append log output to. Also accepts "stderr" as an option..')

    parser.add_argument('--push', action='store_true',
            help='Upload local files that are not already present in the album.')

    parser.add_argument('--pull', action='store_true',
            help='Download album photos that are not already present in the local path. ' +
            '(Careful: when used with --checksum, if checksums are not on Flickr then all local ' +
            'content will be overwridden.)')

    parser.add_argument('--sync', action='store_true',
            help='Synchronize the destination to match the source. After completing a --push or '
                '--pull, remove photos in destination that are not in the source.')

    parser.add_argument('--tag', default='', type=str,
            help='Tag name for Flickr photos. If set, uploads have this tag applied and only ' +
            'photos with this tag are managed by %(prog)s. Allows %(prog)s to only manage a ' +
            'subset of an album, and allows easy searching for all images managed by %(prog)s. ' +
            '(Caution: this could completely change Flickr photos noticed by the app. This not ' +
            'a way to apply the tag to existing photos.)')

    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    return parser.parse_args()


def cli():
    args = getCmdlineArgs()

    # Setup log first. Set log levels for this script, main lib, and the flickrapi dependency.
    if args.logfile == 'stderr':
        logging.basicConfig(stream=sys.stderr)
    else:
        logging.basicConfig(filename=args.logfile)

    logger = logging.getLogger(__name__)
    logger.setLevel(args.loglevel)
    logging.getLogger('flickrsyncr').setLevel(args.loglevel)
    flickrapi.set_log_level(args.loglevel)

    logger.info('Cmd-line args: ' + str(args))

    setupStatus()

    if args.dryrun:
        msg = 'NOTE: Dryrun mode, no changes will be made to local files or Flickr photos.'
        updateStatus(msg)
        logger.warning(msg)

    try:
        # Store settings set from the args.
        config = Config(args.album, args.path,
            api_key=args.api_key,
            api_secret=args.api_secret,
            push=args.push,
            pull=args.pull,
            sync=args.sync,
            tag=args.tag,
            checksum=args.checksum,
            dryrun=args.dryrun,
            dir_=args.config_dir,
            store=loadConfigStore(config_dir=args.config_dir),
        )

        # Do the actual syncing.
        flickrwrapper = getFlickrAPI(config)
        config.album_id = flickrwrapper.getAlbumID(args.album)
        sync(config, flickrwrapper)
    except (SyncError) as e:
        print(e, file=sys.stderr)
        logger.error(e)
        sys.exit(2)


if __name__ == '__main__':
    cli()
