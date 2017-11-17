import configparser
import logging
import os
from flickrsyncr.general import CHECKSUM_TAG_PREFIX
from flickrsyncr.general import CHECKSUM_TAG_PREFIX_NORMALIZED
from flickrsyncr.general import logger
from flickrsyncr.general import SyncError


# The config file to use if none is specified.
DEFAULT_CONFIG_FILE = '~/.config/flickrsyncr/config.conf'


class Settings():
    """Settings for input to flickrsyncr.sync().
    """
    def __init__(self, album, path, api_key='', api_secret='', push=False, pull=False, sync=False,
            tag='', checksum=False, dryrun=False, config_file='', config_profile=''):
        """ album - Name of Flickr album
        path - Local path for photos
        api_key        - Flickr API key. (Required in Settings() or in the config file.)
        api_secret     - Flickr API secret. (Required in Settings() or in the config file.)
        push           - Local is the source, Flickr album is the destination. (aka, upload)
        pull           - Flickr album is the source, local is the destination. (aka, download)
        sync           - Remove all photos at the destination that aren't in the source.
                         (Optional)
        tag            - Ignore all Flickr photos without this tag. Uploaded photos will get the
                         tag. (Optional)
        checksum       - Store the file's checksum on Flickr, use it to detect edits. (Optional)
        dryrun         - Don't make any modifications to photos, locally or on Flickr. (Optional)
        config_file    - File path to use to load config settings. (Optional)
        config_profile - Inside the config file, the profile name to use to load config settings.
                        (Optional)
        """
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

        # Settings that are populated later.
        self.album_id = None
        self.user_id = None

        # Automatically import default API settings if none are provided. Don't throw errors
        # because this may not be setup by the caller.
        if not api_key or not api_secret or config_file:
            try:
                self.importConfigFile(file_path=config_file, section_name=config_profile)
            except Exception:
                pass


    def __str__(self):
        return str(vars(self))

    def importConfigFile(self, file_path='', section_name=''):
        """Adds the settings in 'section_name' from the config file to the Settings object.
        file_path - optional path to the config file, defaults to ~/.config/flickersyncr/config
        section_name - optional name of section to retrieve settings from, defaults to 'default'
        fail_silent - if the config can't be loaded, don't throw any exceptions
        """
        logging.info('Importing config file...')
        if not file_path:
            file_path = os.path.expanduser(DEFAULT_CONFIG_FILE)
        if not section_name:
            section_name = 'DEFAULT'
        logging.info('Importing config, path={}, section={}'.format(file_path, section_name))
        print('Importing config file')

        if not os.path.exists(file_path):
            raise SyncError("Can't load config from path path {}, file doesn't exist".format(file_path))
        config = configparser.ConfigParser()
        config.read(file_path)
        try:
            self.api_key = config.get(section_name, 'api_key')
            self.api_secret = config.get(section_name, 'api_secret')
        except configparser.NoOptionError as e:
            raise SyncError('Options not specified. {}'.format(e))
        except configparser.NoSectionError as e:
            raise SyncError('No config section named "{}": error={}'.format(sectionname, e))

    def validate(self):
        """Validates that the settings meet the necessary logical constraints.
        """
        # The Flickr API key and secret must be specified.
        if not self.api_key or not self.api_secret:
            raise SyncError('The api_key and api_secret must be provided.' +
                    'What was set: api_key={}}, api_secret=%{}}'.format(
                    self.api_key, self.api_secrete))

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

        if ' ' in self.tag:
            raise SyncError('Spaces within tags is unsupported.')
