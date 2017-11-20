#!/usr/bin/env python

import logging
import os
import shutil
import sys
# In case flickrsync isn't installed check the location in the source tree.
try:
    import flickrsyncr
except ImportError:
    sys.path.append('..')
    import flickrsyncr
from flickrsyncr.sync import getPhotosetDifferences
from flickrsyncr.sync import LocalPhoto
from flickrsyncr.sync import RemotePhoto
from flickrsyncr.sync import MismatchedPhoto
from flickrsyncr.sync import createChecksumTag
from flickrsyncr.sync import parseChecksumTag
import flickrsyncr.general

TEST_PICS_DIR = ['./pics1', './pics2']
TEST_SYNC_DIR = './test-sync'
TEST_CONFIG_DIR = './config'

# Set the flickrsync logging level. Also set the flickrapi, but probably don't need as much
# verbosity from it.
TEST_LOG_FILE = './flickrsyncr-lib-test.log'
logging.basicConfig(filename=TEST_LOG_FILE, filemode='w')
flickrsyncr.general.logger.setLevel(logging.DEBUG)
logging.getLogger('flickrapi').setLevel(logging.WARNING)


# Similar to flickrsyncr.sync.createChecksumTag but for the human version of the tag format.
def createHumanChecksumTag(checksum):
    return flickrsyncr.general.CHECKSUM_TAG_PREFIX_NORMALIZED + checksum


def checksumTagUnitTests():
    assert createChecksumTag('abc') == 'checksum:md5=abc'
    assert parseChecksumTag('checksum:md5=abc') == 'abc'
    print('Checksum tag unit tests SUCCEEDED')


def compareLists(list1, list2):
    # str() on a Photo object is good enough to ID it for this case.
    return set(str(list1)) == set(str(list2))


def getPhotosetDifferencesTest(test_num, checksum, local_photos, remote_photos,
        local_only_expected, remote_only_expected, mismatched_expected):
    settings = flickrsyncr.Settings('album', '/path', checksum=checksum,
            config_dir=TEST_CONFIG_DIR)
    local_only, remote_only, mismatched = \
            getPhotosetDifferences(local_photos, remote_photos, settings)

    success = True
    if not compareLists(local_only, local_only_expected):
        print('local only = ' + str(local_only))
        print('local only expected = ' + str(local_only_expected))
        success = False
    if not compareLists(remote_only, remote_only_expected):
        print('remote only = ' + str(remote_only))
        print('remote only expected = ' + str(remote_only_expected))
        success = False
    if not compareLists(mismatched, mismatched_expected):
        print('mismatched = ' + str(mismatched))
        print('mismatched expected = ' + str(mismatched_expected))
        success = False
    return success


def photosetDifferencesUnitTests():
    assert photosetDifferencesUnitTest1()
    assert photosetDifferencesUnitTest2()
    assert photosetDifferencesUnitTest3()
    assert photosetDifferencesUnitTest4()
    assert photosetDifferencesUnitTest5()
    assert photosetDifferencesUnitTest6()
    print('photosetDifferences unit tests SUCCEEDED')


# All local
def photosetDifferencesUnitTest1():
    local_photos = [
            LocalPhoto('1.png', './pics1'),
            LocalPhoto('2.png', './pics1'),
            LocalPhoto('3.png', './pics2'),
    ]
    remote_photos = []

    local_only_expected = local_photos
    remote_only_expected = []
    mismatched_expected = []

    return getPhotosetDifferencesTest(1, False, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


# All remote
def photosetDifferencesUnitTest2():
    local_photos = []
    remote_photos = [
        RemotePhoto('1.png', 1, [createChecksumTag('0123456789abcdef0123456789abcdef')]),
    ]

    local_only_expected = []
    remote_only_expected = remote_photos
    mismatched_expected = []

    return getPhotosetDifferencesTest(2, False, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


# No intersection.
def photosetDifferencesUnitTest3():
    local_photos = [
            LocalPhoto('1.png', './pics1'),
            LocalPhoto('2.png', './pics1'),
            LocalPhoto('3.png', './pics2'),
    ]
    remote_photos = [
        RemotePhoto('4.png', 1, [createChecksumTag('0123456789abcdef0123456789abcdef')]),
        RemotePhoto('5.png', 1, [createChecksumTag('0123456789abcdef0123456789abcdef')]),
    ]

    local_only_expected = local_photos
    remote_only_expected = remote_photos
    mismatched_expected = []

    return getPhotosetDifferencesTest(3, False, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


# Remote subset of Local (no checksums)
def photosetDifferencesUnitTest4():
    local_photos = [
            LocalPhoto('1.png', './pics1'),
            LocalPhoto('2.png', './pics1'),
            LocalPhoto('3.png', './pics2'),
    ]
    remote_photos = [
        RemotePhoto('1.png', 1, [createChecksumTag('0123456789abcdef0123456789abcdef')]),
        RemotePhoto('2.png', 2, [createChecksumTag('0123456789abcdef0123456789abcdef')]),
    ]

    local_only_expected = [
        local_photos[2]
    ]
    remote_only_expected = []
    mismatched_expected = [
        MismatchedPhoto(local_photos[0], remote_photos[0]),
        MismatchedPhoto(local_photos[1], remote_photos[1]),
    ]

    return getPhotosetDifferencesTest(4, True, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


# Remote subset of Local (checksums)
def photosetDifferencesUnitTest5():
    local_photos = [
            LocalPhoto('1.png', './pics1'),
            LocalPhoto('2.png', './pics1'),
            LocalPhoto('3.png', './pics2'),
    ]
    remote_photos = [
        RemotePhoto('1.png', 1, [createChecksumTag('b49e0725b902053edfff8dbfe70872a0')]),
        RemotePhoto('2.png', 2, [createChecksumTag('89c8fdebe17206895d1819ea6224d945')]),
    ]

    local_only_expected = [
        local_photos[2]
    ]
    remote_only_expected = []
    mismatched_expected = []

    return getPhotosetDifferencesTest(4, True, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


# Remote and Local intersect (checksums) with mismatches and both sides have unique elements.
def photosetDifferencesUnitTest6():
    local_photos = [
            LocalPhoto('1.png', './pics1'),
            LocalPhoto('2.png', './pics1'),
            LocalPhoto('3.png', './pics2'),
    ]
    remote_photos = [
        RemotePhoto('3.png', 3, [createChecksumTag('72303bec8d8c9794e2284144e30a265d')]),
        RemotePhoto('4.png', 4, [createChecksumTag('0123456789abcdef0123456789abcdef')]),
        RemotePhoto('1.png', 1, [createChecksumTag('0123456789abcdef0123456789abcdef')]),
    ]

    local_only_expected = [
        local_photos[1],
    ]
    remote_only_expected = [
        remote_photos[1],
    ]
    mismatched_expected = [
        MismatchedPhoto(local_photos[0], remote_photos[2]),
    ]

    return getPhotosetDifferencesTest(5, True, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


# Remote and Local are the same (checksums).
def photosetDifferencesUnitTest6():
    local_photos = [
            LocalPhoto('1.png', './pics1'),
            LocalPhoto('2.png', './pics1'),
            LocalPhoto('3.png', './pics2'),
    ]
    remote_photos = [
        RemotePhoto('3.png', 3, [createChecksumTag('72303bec8d8c9794e2284144e30a265d')]),
        RemotePhoto('2.png', 2, [createChecksumTag('89c8fdebe17206895d1819ea6224d945')]),
        RemotePhoto('1.png', 1, [createChecksumTag('b49e0725b902053edfff8dbfe70872a0')]),
    ]

    local_only_expected = []
    remote_only_expected = []
    mismatched_expected = []

    return getPhotosetDifferencesTest(6, True, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


def pauseVerify(settings, preparation, description=''):
    settings_str = ''
    if settings:
        if settings.push:
            settings_str += '--push '
        if settings.pull:
            settings_str += '--pull '
        if settings.sync:
            settings_str += '--sync '
        if settings.checksum:
            settings_str += '--checksum'
        if settings.tag:
            settings_str += '--tag={} '.format(settings.tag)

    print()
    print('=======================================')
    print('* Finished a test step (program output, if it exists, is above ^)')
    print()
    if settings:
        print('* Settings used:')
        print('===> ' + settings_str)
        print('')
    if preparation:
        print('* Preparation steps performed for the test:')
        print('===> ' + preparation)
        print('')
    if description:
        print('* HUMAN: Verify the test did this and only this (see above settings for why):')
        print('===> ' + description)
        print()
    print('=======================================')
    print('Press <Enter> to move onto the next test...')
    input()


def sync(settings):
    print('---START FLICKRSYNCR EXECUTION OUTPUT---')
    flickrsyncr.sync(settings)
    print('--- END FLICKRSYNCR EXECUTION OUTPUT ---')


def cleanTestSyncDir():
    # Clean out the test syncing dir.
    try:
        shutil.rmtree(TEST_SYNC_DIR)
    except FileNotFoundError:
        pass


def testSyncAddLocalFile(src, files):
    for f in files:
        shutil.copyfile(os.path.join(src, f), os.path.join(TEST_SYNC_DIR, f))


def testSyncDelLocalFile(files):
    for f in files:
        try:
            os.remove(os.path.join(TEST_SYNC_DIR, f))
        except FileNotFoundError:
            pass


def interactiveEndToEndLong():
    pauseVerify(None,
            """Starting interactive test. You will have to verify the actions taken.

    To start:
      * Ensure no other test is running
      * Ensure there is no Flickr album already named "test-sync"
      * Ensure the "pics" directory is in the same directory the test is running in
      * Logs are written to {}, check it for more information on failing tests
      * Run this script from inside it\'s directory.
      * Fill in the api_key and api_secret in tests/config/config.conf
        (remove it when you are done)""".format(TEST_LOG_FILE)
            )

    cleanTestSyncDir()
    os.mkdir(TEST_SYNC_DIR)

    #################
    # Push, sync, checksum
    #################
    settings = flickrsyncr.Settings('test-sync', TEST_SYNC_DIR, push=True, sync=True,
            checksum=True, config_dir=TEST_CONFIG_DIR)

    # Tests:
    #   * Logging in
    #   * Adding to empty album
    #   * Creating album
    #   * Single photo transfer
    testSyncAddLocalFile(TEST_PICS_DIR[0], ['2.png'])
    sync(settings)
    pauseVerify(settings,
            'Added 2.png to local dir',
            'Uploaded 2.png with checksums, created album "test-sync"'
            )

    # Tests:
    #   * Upload ignores files with matching checksums
    #   * Upload partical content match
    #   * Upload multiple files
    #   * Upload subset with mismatched checksums
    #   * Removing the entire album content before uploading more
    testSyncAddLocalFile(TEST_PICS_DIR[0], ['1.png', '3.png', '4.png'])
    testSyncAddLocalFile(TEST_PICS_DIR[1], ['2.png'])
    sync(settings)
    pauseVerify(settings,
            'Added 1.png, 3.png, 4.png to local dir, modified 2.png in local dir ("2 (new)")',
            'Uploaded 1.png, 2.png, 4.png with checksum, uploaded the modified 2.png with checksum'
            )

    # Tests:
    #   * Sync only removing photos.
    #   * Sync removing multiple photos.
    testSyncDelLocalFile(['3.png', '4.png'])
    sync(settings)
    pauseVerify(settings,
            'Deleted 3.png and 4.png from local dir',
            'Deleted 3.png and 4.png from album',
            )

    # Tests:
    #   * Re-syncing with same state should produce no action
    sync(settings)
    pauseVerify(settings,
            'No changes',
            'Nothing should happen'
            )

    #################
    # Pull, sync, checksum
    # (relies on existing state from above)
    #################

    # Prep the album by re-adding 3.png, 4.png. (Uses functionality tested above.)
    testSyncAddLocalFile(TEST_PICS_DIR[0], ['3.png', '4.png'])
    settings = flickrsyncr.Settings('test-sync', TEST_SYNC_DIR, push=True, sync=True,
            checksum=True, config_dir=TEST_CONFIG_DIR)
    sync(settings)

    settings = flickrsyncr.Settings('test-sync', TEST_SYNC_DIR, pull=True, sync=True,
            checksum=True, config_dir=TEST_CONFIG_DIR)

    # Tests:
    #   * Skip download for matched
    #   * Download mismatched checksum
    #   * Download multiple files
    #   * Download missing subset of files
    testSyncAddLocalFile(TEST_PICS_DIR[0], ['2.png'])
    sync(settings)
    pauseVerify(settings,
            'Modified 2.png in local dir (to original), added 3.png and 4.png back into to album',
            'Downloaded the album version of 2.png ("new") overwritting local version, ' +
            'downloaded 3.png and 4.png from album'
            )

    # Tests:
    #   * Downlaod everything to an empty directory.
    testSyncDelLocalFile(['1.png', '2.png', '3.png', '4.png'])
    sync(settings)
    pauseVerify(settings,
            'Removed 1.png, 2.png, 3.png, 4.png from local dir',
            'Downloaded 1.png, 2.png, 3.png, 4.png'
            )

    #################
    # Pull
    # (relies on existing state from above)
    #################

    # Prep the album by removing 4.png. (Uses functionality tested above.)
    testSyncDelLocalFile(['4.png'])
    settings = flickrsyncr.Settings('test-sync', TEST_SYNC_DIR, push=True, sync=True,
            checksum=True, config_dir=TEST_CONFIG_DIR)
    sync(settings)

    settings = flickrsyncr.Settings('test-sync', TEST_SYNC_DIR, pull=True,
            config_dir=TEST_CONFIG_DIR)

    # Tests:
    #   * Not removing extra local files
    #   * Downloading a subset of missing photos.
    testSyncDelLocalFile(['2.png'])
    testSyncAddLocalFile(TEST_PICS_DIR[0], ['4.png'])
    sync(settings)
    pauseVerify(settings,
            'Added 4.png and removed 2.png in local dir',
            'Downloaded 2.png'
            )

    # Tests;
    #   * Ignoring mismatched checksums
    testSyncAddLocalFile(TEST_PICS_DIR[0], ['2.png'])
    sync(settings)
    pauseVerify(settings,
            'Modified 2.png in local dir.',
            'Nothing should happen'
            )

    #################
    # Push
    # (relies on existing state from above)
    #################

    # Tests:
    #   * Ignoring mismatching checksum
    #   * Uploading missing content
    settings = flickrsyncr.Settings('test-sync', TEST_SYNC_DIR, push=True,
            config_dir=TEST_CONFIG_DIR)
    sync(settings)
    pauseVerify(settings,
            'Modified 2.png (in previous step) and added 4.png in local dir',
            '4.png should upload with no checksum (2.png should not be uploaded)'
            )

    #################
    # Tags
    # (relies on existing state from above)
    #################

    # Tests:
    #   * Setting tags on uploads
    #   * Re-uploading photos even if they exist un-tagged
    settings = flickrsyncr.Settings('test-sync', TEST_SYNC_DIR, push=True, tag='customtag',
            config_dir=TEST_CONFIG_DIR)
    testSyncDelLocalFile(['3.png', '4.png'])
    sync(settings)
    pauseVerify(settings,
            'Removed 3.png, 4.png from local dir.',
            '1.png, 2.png should duplicate in album with tag value "customtag"'
            )

    # Tests:
    #   * Download tag-matching photos.
    #   * Don't download photos missing mismatching the tag.
    settings = flickrsyncr.Settings('test-sync', TEST_SYNC_DIR, pull=True, tag='customtag',
            config_dir=TEST_CONFIG_DIR)
    testSyncDelLocalFile(['2.png', '3.png'])
    sync(settings)
    pauseVerify(settings,
            'Removed 2.png, 3.png from local dir',
            'Downloaded 2.png (and not 3.png due to the tag value)'
            )

    #################
    # Done
    # (relies on existing state from above)
    #################

    # Tests:
    #   * Uploading empty dir
    settings = flickrsyncr.Settings('test-sync', TEST_SYNC_DIR, push=True, sync=True,
            config_dir=TEST_CONFIG_DIR)
    testSyncDelLocalFile(['1.png', '2.png', '3.png', '4.png'])
    sync(settings)
    pauseVerify(settings,
            'Removed all local files',
            'Deleted the album (due to the push removing all contents)'
            )

    cleanTestSyncDir()
    print('Interative end-to-end test DONE: Human must verify results are expected.')


def interactiveEndToEndShort():
    pass


def main():
    checksumTagUnitTests()
    photosetDifferencesUnitTests()
    interactiveEndToEndShort()
    interactiveEndToEndLong()

if __name__ == '__main__':
    main()
