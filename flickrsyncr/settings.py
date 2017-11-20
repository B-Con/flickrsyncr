import configparser
import logging
import os
from flickrsyncr.general import CHECKSUM_TAG_PREFIX
from flickrsyncr.general import CHECKSUM_TAG_PREFIX_NORMALIZED
from flickrsyncr.general import logger
from flickrsyncr.general import SyncError


# The default config path.
DEFAULT_CONFIG_DIR = '~/.config/flickrsyncr'
# The default section name in the config.
DEFAULT_SECTION_NAME = 'DEFAULT'
# The config filename where settings are stored.
CONFIG_FILENAME = 'config.conf'


class Settings():
    """Settings for input to flickrsyncr.sync().

    Supported parameters to __init__().

    album
        Name of Flickr album
    path
        Local path for photos
    api_key
        Flickr API key. (Required in Settings() or in the config file.)
    api_secret
        Flickr API secret. (Required in Settings() or in the config file.)
    push
        Local is the source, Flickr album is the destination. (aka, upload)
    pull
        Flickr album is the source, local is the destination. (aka, download)
    sync
        Remove all photos at the destination that aren't in the source. (Optional)
    tag
        Ignore all Flickr photos without this tag. Uploaded photos will get the tag. (Optional)
    checksum
        Store the file's checksum on Flickr, use it to detect edits. (Optional)
    dryrun
        Don't make any modifications to photos, locally or on Flickr. (Optional)
    config_dir
        Base path to use for loading/storing config settings. (Optional)
    config_profile
        Inside the config file, the profile name to use to load config settings. (Optional)
        """
    def __init__(self, album, path, api_key='', api_secret='', push=False, pull=False, sync=False,
            tag='', checksum=False, dryrun=False, config_dir='', config_profile=''):
        # User-provided settings.
        self.album = album
        self.path = path
        self.push = push
        self.pull = pull
        self.sync = sync
        self.tag = tag
        self.checksum = checksum
        self.dryrun = dryrun
        self.api_key = api_key
        self.api_secret = api_secret
        self.config_dir = os.path.expanduser(config_dir if config_dir else DEFAULT_CONFIG_DIR)
        self.config_profile = config_profile if config_profile else DEFAULT_SECTION_NAME

        # Settings that are populated later.
        self.album_id = None
        self.user_id = None

        # Automatically import default API settings if none are provided.
        self.importConfig()

    def __str__(self):
        return str(vars(self))

    def importConfig(self):
        """Adds the settings in 'section_name' from the config file to the Settings object.
        Only imports settings not explicitly provided.
        """
        file_path = os.path.join(self.config_dir, CONFIG_FILENAME)
        logging.info('Importing config, path={}, section={}'.format(file_path,
                self.config_profile))
        if not os.path.exists(file_path):
            raise SyncError("Can't load config from path {}, file doesn't exist".format(file_path))
        config = configparser.ConfigParser()
        config.read(file_path)

        if not self.api_key:
            self.api_key = self._importConfigOption(config, 'api_key')
        if not self.api_secret:
            self.api_secret = self._importConfigOption(config, 'api_secret')
        # TODO: Import the rest of the settings? If so need to explicitly track how they were set.

    def _importConfigOption(self, config, option_name):
        try:
            option_value = config.get(self.config_profile, option_name)
        except configparser.NoOptionError as e:
            raise SyncError('Option {} not in config file: {}'.format(option_name, e))
        except configparser.NoSectionError as e:
            raise SyncError('No config section "{}": error={}'.format(self.config_profile, e))
        return option_value

    def validate(self):
        """Validates that the settings meet the necessary logical constraints.
        """
        # The Flickr API key and secret must be specified.
        if not self.api_key:
            raise SyncError('The api_key must be provided, but it was not. Get one from ' +
                    'http://www.flickr.com/services/api/keys/ .')
        if not self.api_secret:
            raise SyncError('The api_secret must be provided, but it was not. Get one from ' +
                    'http://www.flickr.com/services/api/keys/ .')

        # User must specify at least --push or --pull.
        if not self.push and not self.pull:
            raise SyncError('You must choose at least one action between --push or --pull. ' +
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

        # Don't let the custom tag start with the checksum tag's prefix, it may confuse checksum
        # syncing logic.
        if self.tag.startswith(CHECKSUM_TAG_PREFIX) or self.tag.startswith(
                CHECKSUM_TAG_PREFIX_NORMALIZED):
            raise SyncError('Specified tag name overlaps with the checksum tag, this will cause ' +
                    'confusion during checksum validation.')

        # Doesn't catch all whitespace, but we explicitly parse by splitting on space. Presumably
        # the others are safe.
        if ' ' in self.tag:
            raise SyncError('Spaces in tag values is unsupported.')
