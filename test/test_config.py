from os.path import expanduser
import unittest

import pyfakefs.fake_filesystem_unittest

# Offically exported names.
from flickrsyncr import Config
from flickrsyncr import loadConfigStore
from flickrsyncr import SyncError


dict_store = {
    "api_key": "abc",
    "api_secret": "123",
}

flat_store = """[DEFAULT]
api_key = abc
api_secret = 123
"""


class StubStore():
    """A test stub to provide config options. Matches API of "configparser"."""
    store = dict_store

    def get(self, profile, option):
        return self.store[option]


class TestConfig(unittest.TestCase):
    def testValidConfig(self):
        """Tests valid config options, including loading api settings from a store.
        """
        testCases = [
            Config('albumname', '/my/dir', '/my/cfg', store=StubStore(), pull=True, dryrun=True),
            Config('albumname', '/my/dir', '/my/cfg', store=StubStore(), push=True, sync=True),
            Config('albumname', '/my/dir', '/my/cfg', store=StubStore(), push=True, sync=True, checksum=True),
            Config('albumname', '/my/dir', '/my/cfg', store=StubStore(), push=True),
            Config('albumname', '/my/dir', '/my/cfg', api_key='apikey', api_secret='apisecret', pull=True)
        ]

        for t in testCases:
            try:
                t.validate()
            except Exception as e:
                self.fail('Setting.validate({}) raised exception "{}"'.format(t, e))

    def testInvalidConfig(self):
        """Tests invalid config options."""
        testCases = [
            # Pull, push, checksum
            Config('albumname', '/my/dir', dir_='/my/cfg', store=StubStore(), pull=True, push=True, checksum=True),
            # No pull or push.
            Config('albumname', '/my/dir', dir_='/my/cfg', store=StubStore(), checksum=True),
            # Pull, push, sync
            Config('albumname', '/my/dir', dir_='/my/cfg', store=StubStore(), pull=True, push=True, sync=True),
            # No store to provide api_key and api_secret.
            Config('albumname', '/my/dir', dir_='/my/cfg', push=True),
        ]

        for t in testCases:
            self.assertRaises(SyncError, t.validate)


class TestLoadConfigStore(pyfakefs.fake_filesystem_unittest.TestCase):
    """Tests that loadConfigStore retrieves config stores."""
    def setUp(self):
        self.setUpPyfakefs()
        self.store_content = flat_store

    def testDefaultPath(self):
        self.fs.create_file(expanduser('~/.config/flickrsyncr/config'),
                contents=self.store_content)
        testCases = [
            Config('albumname', '/my/dir', store=loadConfigStore(), push=True),
            Config('albumname', '/my/dir', store=loadConfigStore(config_dir=''), push=True),
        ]

        for t in testCases:
            try:
                t.validate()
            except Exception as e:
                self.fail('Setting.validate({}) raised exception "{}"'.format(t, e))

    def testCustomPath(self):
        self.fs.create_file('/tmp/config', contents=self.store_content)
        t = Config('albumname', '/my/dir', store=loadConfigStore('/tmp'), push=True)
        try:
            t.validate()
        except Exception as e:
            self.fail('Setting.validate({}) raised exception "{}"'.format(t, e))

if __name__ == '__main__':
    unittest.main()
