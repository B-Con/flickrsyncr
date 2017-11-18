#!/usr/bin/env python

import logging
import shutil
import sys
# In case flickrsync isn't installed already.
try:
    import flickrsyncr
except ImportError:
    sys.path.append('../flickrsync')
    import flickrsyncr
from flickrsyncr.sync import getPhotosetDifferences
from flickrsyncr.sync import LocalPhoto
from flickrsyncr.sync import RemotePhoto
from flickrsyncr.sync import MismatchedPhoto
from flickrsyncr.sync import createChecksumTag
from flickrsyncr.sync import parseChecksumTag
import flickrsyncr.general


# Set the flickrsync logging level.
TEST_LOG_FILE = './flickrsyncr-lib-test.log'
logging.basicConfig(filename=TEST_LOG_FILE, filemode='w')
flickrsyncr.general.logger.setLevel(logging.DEBUG)
logging.getLogger('flickrapi').setLevel(logging.DEBUG)


# Similar to flickrsyncr.sync.createChecksumTag but for the human version of the tag format.
def createHumanChecksumTag(checksum):
    return flickrsyncr.general.CHECKSUM_TAG_PREFIX_NORMALIZED + checksum


def checksumTagUnitTests():
    assert createChecksumTag('abc') == 'checksum:md5=abc'
    assert parseChecksumTag('checksummd5abc') == 'abc'
    print('Checksum tag unit tests SUCCEEDED')


def compareLists(list1, list2):
    # str() on a Photo object is good enough to ID it for this case.
    return set(str(list1)) == set(str(list2))


def getPhotosetDifferencesTest(test_num, checksum, local_photos, remote_photos,
        local_only_expected, remote_only_expected, mismatched_expected):
    settings = flickrsyncr.Settings('album', '/path', checksum=checksum)
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
            LocalPhoto('1.png', './pics1-orig'),
            LocalPhoto('2.png', './pics1-orig'),
            LocalPhoto('3.png', './pics2-orig'),
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
        RemotePhoto('1.png', 1, [createHumanChecksumTag('0123456789abcdef0123456789abcdef')]),
    ]

    local_only_expected = []
    remote_only_expected = remote_photos
    mismatched_expected = []

    return getPhotosetDifferencesTest(2, False, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


# No intersection.
def photosetDifferencesUnitTest3():
    local_photos = [
            LocalPhoto('1.png', './pics1-orig'),
            LocalPhoto('2.png', './pics1-orig'),
            LocalPhoto('3.png', './pics2-orig'),
    ]
    remote_photos = [
        RemotePhoto('4.png', 1, [createHumanChecksumTag('0123456789abcdef0123456789abcdef')]),
        RemotePhoto('5.png', 1, [createHumanChecksumTag('0123456789abcdef0123456789abcdef')]),
    ]

    local_only_expected = local_photos
    remote_only_expected = remote_photos
    mismatched_expected = []

    return getPhotosetDifferencesTest(3, False, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


# Remote subset of Local (no checksums)
def photosetDifferencesUnitTest4():
    local_photos = [
            LocalPhoto('1.png', './pics1-orig'),
            LocalPhoto('2.png', './pics1-orig'),
            LocalPhoto('3.png', './pics2-orig'),
    ]
    remote_photos = [
        RemotePhoto('1.png', 1, [createHumanChecksumTag('0123456789abcdef0123456789abcdef')]),
        RemotePhoto('2.png', 2, [createHumanChecksumTag('0123456789abcdef0123456789abcdef')]),
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
            LocalPhoto('1.png', './pics1-orig'),
            LocalPhoto('2.png', './pics1-orig'),
            LocalPhoto('3.png', './pics2-orig'),
    ]
    remote_photos = [
        RemotePhoto('1.png', 1, [createHumanChecksumTag('b49e0725b902053edfff8dbfe70872a0')]),
        RemotePhoto('2.png', 2, [createHumanChecksumTag('89c8fdebe17206895d1819ea6224d945')]),
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
            LocalPhoto('1.png', './pics1-orig'),
            LocalPhoto('2.png', './pics1-orig'),
            LocalPhoto('3.png', './pics2-orig'),
    ]
    remote_photos = [
        RemotePhoto('3.png', 3, [createHumanChecksumTag('72303bec8d8c9794e2284144e30a265d')]),
        RemotePhoto('4.png', 4, [createHumanChecksumTag('0123456789abcdef0123456789abcdef')]),
        RemotePhoto('1.png', 1, [createHumanChecksumTag('0123456789abcdef0123456789abcdef')]),
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
            LocalPhoto('1.png', './pics1-orig'),
            LocalPhoto('2.png', './pics1-orig'),
            LocalPhoto('3.png', './pics2-orig'),
    ]
    remote_photos = [
        RemotePhoto('3.png', 3, [createHumanChecksumTag('72303bec8d8c9794e2284144e30a265d')]),
        RemotePhoto('2.png', 2, [createHumanChecksumTag('89c8fdebe17206895d1819ea6224d945')]),
        RemotePhoto('1.png', 1, [createHumanChecksumTag('b49e0725b902053edfff8dbfe70872a0')]),
    ]

    local_only_expected = []
    remote_only_expected = []
    mismatched_expected = []

    return getPhotosetDifferencesTest(6, True, local_photos, remote_photos, local_only_expected, remote_only_expected, mismatched_expected)


def pauseVerify(test_num, settings, happened, state):
    print('=======================================')
    print('* Finished test step #{} (program output, if it exists, is above ^)'.format(test_num))
    print('* Settings used:\n===> ' + str(settings) + '\n')
    print('* Here is what should have just happened:\n===> ' + happened + '\n')
    print('* HUMAN: Please verify the following state:\n===> ' + state + '\n')
    print('Press <Enter> to move onto the next test...')
    input()


def sync(settings):
    print('===START FLICKRSYNCR EXECUTION OUTPUT===')
    flickrsyncr.sync(settings)
    print('===END FLICKRSYNCR EXECUTION OUTPUT===')


def cleanTestFolders():
    # Clean out the old temp working sync dirs.
    try:
        shutil.rmtree('pics1-sync')
        shutil.rmtree('pics2-sync')
        shutil.rmtree('pics3-sync')
    except FileNotFoundError:
        pass


def interactiveEndToEnd():
    pauseVerify(0, None,
            'Dummy step, now starting tests.',
            'Ensure no other tests running, no album is named "test-sync", and "pics1-orig", ' +
            '"pics2-orig", and "pics3-orig" are in the same directory. Logs are written to ' +
            TEST_LOG_FILE + ', check it for more information if a test fails.')

    cleanTestFolders()
    shutil.copytree('pics1-orig', 'pics1-sync')
    shutil.copytree('pics2-orig', 'pics2-sync')
    shutil.copytree('pics3-orig', 'pics3-sync')
    pauseVerify(1, None,
            'Make local folder copies for syncing and manipulating.',
            'Ensure "pics1-sync", "pics2-sync", and "pics3-sync" are local folders with the ' +
            'same contents as their "-orig" counterparts.')

    settings = flickrsyncr.Settings('test-sync', './pics1-sync', push=True, sync=False, checksum=True)
    sync(settings)
    pauseVerify(2, settings,
            'Uploaded "1.png", uploaded "2.png" with checksums, created album "test-sync"',
            'Album "test-sync" has "1.png" and "2.png"')

    settings = flickrsyncr.Settings('test-sync', './pics2-sync', push=True, sync=False, checksum=False)
    sync(settings)
    pauseVerify(3, settings,
            'Skipped uploading "2.png" (despite checksum mismatch), uploaded "3.png", didn\'t ' +
            'remove "1.png" (sync disabled)',
            'Album "test-sync" has "1.png", the same "2.png", and "3.png"')

    settings = flickrsyncr.Settings('test-sync', './pics2-sync', push=True, sync=True, checksum=True)
    sync(settings)
    pauseVerify(4, settings,
            'Uploaded "2.png" (checksum mismatch), uploaded "3.png" (no checksum), deleted ' +
            '"1.png" (sync enabled)',
            'Album "test-sync" has the new "2.png" and has "3.png"')

    settings = flickrsyncr.Settings('test-sync', './pics2-sync', push=True, sync=True, checksum=True)
    sync(settings)
    pauseVerify(5, settings,
            'Same sync settings as last time',
            'Album "test-sync" has not changed and no uploads or deletes happened')

    settings = flickrsyncr.Settings('test-sync', './pics2-sync', pull=True, sync=True, checksum=True)
    sync(settings)
    pauseVerify(6, settings,
            'Same sync settings as last time, except this time it pulls',
            'Folder "pics2-sync" has not changed and equals "pics2-orig".')

    settings = flickrsyncr.Settings('test-sync', './pics3-sync', pull=True, sync=True, checksum=False)
    sync(settings)
    pauseVerify(7, settings,
            'Ignored "2.png" (despite mismatched checksum), downloaded "3.png", and removed ' +
            '"4.png" in "./pics3-sync"',
            'Folder "pics3-sync" has the old "2.png" and "3.png"')

    settings = flickrsyncr.Settings('test-sync', './pics3-sync', pull=True, sync=True, checksum=True)
    sync(settings)
    pauseVerify(8, settings,
            'Downloaded "2.png" (due to mismatched checksum)',
            'The new "2.png" and the same "3.png" are in "./pics3-sync"')

    settings = flickrsyncr.Settings('test-sync', './pics2-sync', pull=True, sync=True, checksum=True, tag='customtag')
    sync(settings)
    pauseVerify(9, settings,
            'Removed everything in "./pics2-sync" by pull and syncing pics with tag "customtag"',
            'There are no photos in Flickr albume with the tag value "customtag" and the ' +
            'contents of "./pics2-sync" are gone.')

    settings = flickrsyncr.Settings('test-sync', './pics3-sync', push=True, sync=True, checksum=True, tag='customtag')
    sync(settings)
    pauseVerify(10, settings,
            'Re-uploaded "1.png", "2.png", and "3.png" with the tag value "customtag"',
            'The existing Flickr photos still exist and there is a new identical "2.png" and ' +
            '"3.png" in the album with the tag value "customtag".')

    cleanTestFolders()
    print('Interative end-to-end test DONE: Human must verify results are expected.')


def customOneOff():
    settings = flickrsyncr.Settings('test-sync', '/tmp/pic', push=True, sync=True, checksum=True, tag='customtag')
    flickrsyncr.sync(settings)


def main():
    checksumTagUnitTests()
    photosetDifferencesUnitTests()
    interactiveEndToEnd()
    #customOneOff()

if __name__ == '__main__':
    main()

