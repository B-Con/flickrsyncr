"""Configuration store, retrieval, validation, and supporting functionality."""
import configparser
import logging
import os

from .general import CHECKSUM_TAG_PREFIX
from .general import CHECKSUM_TAG_PREFIX_NORMALIZED
from .general import SyncError

DEFAULT_CONFIG_DIR = '~/.config/flickrsyncr'
DEFAULT_SECTION_NAME = 'DEFAULT'
CONFIG_FILENAME = 'config'


__all__ = ['Config', 'loadConfigStore']
logger = logging.getLogger(__name__)


class Config():
    """Config for input to flickrsyncr.sync().

    Args:
        album: Name of Flickr album
        path: Local path for photos
        api_key: Flickr API key. (Required in Config() or in the config file.)
        api_secret: Flickr API secret. (Required in Config() or in the config file.)
        dir_: Dir with config file and local OAuth tokens.
        push: Local is the source, Flickr album is the destination. (aka, upload)
        pull: Flickr album is the source, local is the destination. (aka, download)
        sync: Remove all photos at the destination that aren't in the source. (Optional)
        tag: Ignore Flickr photos without this tag. Uploaded photos will get the tag. (Optional)
        checksum: Store the file's checksum on Flickr, use it to detect edits. (Optional)
        dryrun: Don't make any modifications to photos, locally or on Flickr. (Optional)
        store: Supports .get(setting_name) for reading config values.
    """
    def __init__(self, album, path, dir_='', api_key=None, api_secret=None, push=False,
            pull=False, sync=False, tag=None, checksum=False, dryrun=False, store=None):
        # User-provided Config.
        self.album = album
        self.path = path
        self.dir_ = os.path.expanduser(dir_ if dir_ else DEFAULT_CONFIG_DIR)
        self.push = push
        self.pull = pull
        self.sync = sync
        self.tag = tag
        self.checksum = checksum
        self.dryrun = dryrun
        self.api_key = api_key
        self.api_secret = api_secret

        # Config that are populated later.
        self.album_id = None

        # Import from the data store.
        if store:
            self.fillFromStore(store)

    def __str__(self):
        return str(vars(self))

    def fillFromStore(self, store):
        """Adds config settings from the config store, eg. a file. Only imports settings from
        config store that are a) necessary and b) not explicitly provided. Throws a SyncError
        if a required parameter can't be found in config.

        Args:
            store: A config store obtained from load_config_store().
        """
        if not self.api_key:
            logger.info('Filling setting "api_key" config store.')
            self.api_key = self._loadSetting(store, 'api_key')
        if not self.api_secret:
            logger.info('Filling setting "api_secret" config store.')
            self.api_secret = self._loadSetting(store, 'api_secret')

    def _loadSetting(self, store, setting_name):
        """Load a setting from config store. Throws an exception if it isn't found.
        """
        setting_val = None
        try:
            setting_val = store.get(DEFAULT_SECTION_NAME, setting_name)
        except configparser.NoSectionError as e:
            # The section doesn't exist at all.
            raise SyncError('No config section "{}": error={}'.format(DEFAULT_SECTION_NAME, e))
        except configparser.NoOptionError as e:
            # A setting with that name doesn't exist.
            raise SyncError

        return setting_val

    def validate(self):
        """Validates that the Config's existing combination of settings is valid."""
        # The Flickr API key and secret must be specified.
        if not self.api_key:
            raise SyncError('api_key must be provided, but it was not. Get one from ' +
                    'http://www.flickr.com/services/api/keys/ .')
        if not self.api_secret:
            raise SyncError('api_secret must be provided, but it was not. Get one from ' +
                    'http://www.flickr.com/services/api/keys/ .')

        # The config dir must be specified.
        if not self.dir_:
            raise SyncError('dir_ must be specified, but it was not.')

        # User must specify at least --push or --pull.
        if not self.push and not self.pull:
            raise SyncError('Choose at least one action between --push or --pull. ' +
                    'What was set: push={}, pull={}'.format(self.push, self.pull))

        # User can both push and pull, but pruning as well is logically useless: There's nothing
        # to prune.
        if self.push and self.pull and self.sync:
            raise SyncError('Specifying --push and --pull and --sync all together makes no ' +
                    'sense, nothing to remove. Choose at most two of them.' +
                    'What was set: push={}, pull={}, sync={}'.format(
                    self.push, self.pull, self.sync))

        # User can both push and pull, but validating checksums at the same time doesn't make
        # sense: Which side wins if the checksum doesn't match?
        if self.push and self.pull and self.checksum:
            raise SyncError('Specifying --push and --pull and --checksum all together makes no ' +
                    'sense, which side\'s checksum is right? Choose at most two of them.' +
                    'What was set: push={}, pull={}, checksum={}'.format(
                    self.push, self.pull, self.checksum))

        # Don't let the custom tag start with the checksum tag's prefix, it will confuse checksum
        # syncing logic.
        if self.tag and (self.tag.startswith(CHECKSUM_TAG_PREFIX) or self.tag.startswith(
                CHECKSUM_TAG_PREFIX_NORMALIZED)):
            raise SyncError('Tag name "{}" overlaps with the checksum tag"{}", this would cause ' +
                    'problems during checksum validation.'.format(self.tag, CHECKSUM_TAG_PREFIX))

        # The only whitespace used is the standard space. Don't know how Flickr would treat other
        # whitespace in tag names.
        if self.tag and ' ' in self.tag:
            raise SyncError('Do not put spaces in tags.')


def loadConfigStore(config_dir=''):
    """Provides a reader for config file. If config_dir is empty, uses a default."""
    dir_path = os.path.expanduser(config_dir if config_dir else DEFAULT_CONFIG_DIR)
    file_path = os.path.join(dir_path, CONFIG_FILENAME)
    if not os.path.exists(file_path):
        raise SyncError("Can't load config from path {}, file doesn't exist".format(file_path))
    logging.info('Reading config from path={}'.format(file_path))
    config = configparser.ConfigParser()
    config.read(file_path)
    return config
