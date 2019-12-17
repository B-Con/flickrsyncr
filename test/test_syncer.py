import unittest
import os

import pyfakefs.fake_filesystem_unittest

# Testing support.
from test.stub_flickrapi import StubFlickrAPI
from test.stub_flickrapi import small_jpg
import flickrsyncr.flickrwrapper  # Import only so it can be patched with stubs.
# Officially exported names.
from flickrsyncr import Config
from flickrsyncr import sync
# Unexported names for targetted whitebox testing.
from flickrsyncr.flickrwrapper import FlickrWrapper
from flickrsyncr.syncer import LocalPhoto
from flickrsyncr.syncer import RemotePhoto
from flickrsyncr.syncer import loadRemotePhotos
from flickrsyncr.syncer import loadLocalPhotos


class TestLocalPhoto(pyfakefs.fake_filesystem_unittest.TestCase):
	"""Tests for the sync.LocalPhoto class. (It's not exported, but convenient to test.)
	"""
	def setUp(self):
		self.setUpPyfakefs()
		self.stub_api = StubFlickrAPI()
		flickrwrapper = FlickrWrapper(self.stub_api, 'userid')
		self.photo = LocalPhoto(flickrwrapper, 'filename.jpg', '/tmp')

		# Create the file we'll operate on.
		self.fs.create_file('/tmp/filename.jpg', contents=small_jpg)

	def testDelete(self):
		config = Config('albumname', '/tmp', checksum=True)
		self.assertTrue(os.path.exists('/tmp/filename.jpg'))
		self.photo.delete(config)
		self.assertFalse(os.path.exists('/tmp/filename.jpg'))

	def testChecksum(self):
		self.assertEqual(self.photo.checksum(), '8c90748342f19b195b9c6b4eff742ded')

	def testUploadWithNoAlbum(self):
		# Upload to a non-existent album, denoted by empty album_id.
		config = Config('albumname', '/tmp', checksum=True)
		self.photo.transfer(config)
		self.assertNotEqual(config.album_id, None)  # album_id init value is None.

	def testUploadWithExistingAlbum(self):
		self.stub_api.stubAddAlbum('albumname', 123)
		config = Config('albumname', '/tmp', checksum=True)
		config.album_id = 123
		self.photo.transfer(config)
		self.assertEqual(config.album_id, 123)


class TestRemotePhoto(pyfakefs.fake_filesystem_unittest.TestCase):
	"""Tests for the sync.RemotePhoto class. (It's not exported, but convenient to test.)
	"""
	def setUp(self):
		self.setUpPyfakefs()
		self.stub_api = StubFlickrAPI()
		flickrwrapper = FlickrWrapper(self.stub_api, 'userid')
		self.photo = RemotePhoto(flickrwrapper, 'filename.jpg', 'photoid123',
				['tag1', 'checksum:md5=8c90748342f19b195b9c6b4eff742ded'])

		self.stub_api.stubAddAlbum('albumname', 123)
		self.stub_api.stubAddPhoto(123, self.photo.title, self.photo.photo_id,
				' '.join(self.photo.tags), small_jpg)

		flickrsyncr.flickrwrapper.urllib.request.urlopen = self.stub_api.stubURLOpenner()

	def testDelete(self):
		config = Config('albumname', '/tmp', checksum=True)
		self.photo.delete(config)

	def testGetChecksum(self):
		self.assertEqual(self.photo.checksum(), '8c90748342f19b195b9c6b4eff742ded')

	def testTransfer(self):
		config = Config('albumname', '/tmp', checksum=True)
		config.album_id = 123
		self.photo.transfer(config)

		with open('/tmp/filename.jpg', 'rb') as f:
			self.assertEqual(f.read(), small_jpg)

class TestGetPhotos(pyfakefs.fake_filesystem_unittest.TestCase):
	"""Tests for the loadLocalPhotos and loadRemotePhotos methods. (It's not exported, but
	convenient to test.)
	"""
	def testLoadLocalPhotos(self):
		self.setUpPyfakefs()
		self.fs.create_file('/tmp/filename1.jpg', contents=small_jpg)
		self.fs.create_file('/tmp/filename2.jpg', contents=small_jpg)
		self.fs.create_file('/tmp/filename3.jpg', contents=small_jpg)

		flickrwrapper = FlickrWrapper(StubFlickrAPI(), 'userid')
		config = Config('albumname', '/tmp', checksum=True)

		want = [
			LocalPhoto(flickrwrapper, 'filename1.jpg', '/tmp'),
			LocalPhoto(flickrwrapper, 'filename2.jpg', '/tmp'),
			LocalPhoto(flickrwrapper, 'filename3.jpg', '/tmp'),
		]
		got = loadLocalPhotos(config, flickrwrapper)
		self.assertEqual(sorted(want), sorted(got))

	def testLoadRemotePhotos(self):
		self.stub_api = StubFlickrAPI()
		flickrwrapper = FlickrWrapper(self.stub_api, 'userid')
		config = Config('albumname', '/tmp', checksum=True)
		config.album_id = 123

		self.stub_api.stubAddAlbum(config.album, config.album_id)
		self.stub_api.stubAddPhoto(123, 'Photo 1', '1111', 'tag1 tag2 tag3', b'')
		self.stub_api.stubAddPhoto(123, 'Photo 2', '2222', 'tag1', b'')
		self.stub_api.stubAddPhoto(123, 'Photo 3', '3333', 'tag2 tag3', b'')
		self.stub_api.stubAddPhoto(123, 'Photo 4', '4444', '', b'')

		want = [
			RemotePhoto(flickrwrapper, 'Photo 1', '1111', ['tag1', 'tag2', 'tag3']),
			RemotePhoto(flickrwrapper, 'Photo 2', '2222', ['tag1']),
			RemotePhoto(flickrwrapper, 'Photo 3', '3333', ['tag2', 'tag3']),
			RemotePhoto(flickrwrapper, 'Photo 4', '4444', []),
		]
		got = loadRemotePhotos(config, flickrwrapper)
		sort_key = lambda p: p.title
		self.assertEqual(sorted(want, key=sort_key), sorted(got, key=sort_key))

class TestSync(pyfakefs.fake_filesystem_unittest.TestCase):
	"""Test the sync() function. (Finally, something that's actually intended for export.)
	"""
	def setUp(self):
		self.setUpPyfakefs()
		self.stub_api = StubFlickrAPI()
		self.flickrwrapper = FlickrWrapper(self.stub_api, 'userid')
		flickrsyncr.flickrwrapper.urllib.request.urlopen = self.stub_api.stubURLOpenner()

	def testPullCleanMerge(self):
		"""Pull, merge distinct local and remote content."""
		self.fs.create_file('/tmp/filename0.jpg', contents=small_jpg+b'0')

		config = Config('albumname', '/tmp', api_key='apikey', api_secret='apisecret',
				checksum=True, pull=True)
		config.album_id = 123

		self.stub_api.stubAddAlbum(config.album, config.album_id)
		self.stub_api.stubAddPhoto(config.album_id, 'filename1.jpg', 'filename1.jpg', 'tag',
				small_jpg+b'1')
		self.stub_api.stubAddPhoto(config.album_id, 'filename2.jpg', 'filename2.jpg', 'tag',
				small_jpg+b'2')

		sync(config, self.flickrwrapper)

		# Verify local file is untouched.
		with open('/tmp/filename0.jpg', 'rb') as f:
			self.assertEqual(f.read(), small_jpg+b'0')

		# Verify remote files downloaded.
		with open('/tmp/filename1.jpg', 'rb') as f:
			self.assertEqual(f.read(), small_jpg+b'1')
		with open('/tmp/filename2.jpg', 'rb') as f:
			self.assertEqual(f.read(), small_jpg+b'2')

	def testPullFavorLocal(self):
		"""Pull, don't overwrite mismatched local content."""
		self.fs.create_file('/tmp/filename0.jpg', contents=b'bad content')

		config = Config('albumname', '/tmp', api_key='apikey', api_secret='apisecret', pull=True)
		config.album_id = 123

		self.stub_api.stubAddAlbum(config.album, config.album_id)
		self.stub_api.stubAddPhoto(config.album_id, 'filename0.jpg', 'filename0.jpg', 'tag',
				small_jpg+b'0')
		self.stub_api.stubAddPhoto(config.album_id, 'filename1.jpg', 'filename1.jpg', 'tag',
				small_jpg+b'1')
		self.stub_api.stubAddPhoto(config.album_id, 'filename2.jpg', 'filename2.jpg', 'tag',
				small_jpg+b'2')

		sync(config, self.flickrwrapper)

		# Verify local file is untouched.
		with open('/tmp/filename0.jpg', 'rb') as f:
			self.assertEqual(f.read(), b'bad content')

		# Verify remote files exist.
		with open('/tmp/filename1.jpg', 'rb') as f:
			self.assertEqual(f.read(), small_jpg+b'1')
		with open('/tmp/filename2.jpg', 'rb') as f:
			self.assertEqual(f.read(), small_jpg+b'2')

	def testPullOverwriteLocal(self):
		"""Pull, overwrite mismatched local content."""
		self.fs.create_file('/tmp/filename0.jpg', contents=b'bad content')

		config = Config('albumname', '/tmp', api_key='apikey', api_secret='apisecret',
				checksum=True, pull=True, sync=True)
		config.album_id = 123

		self.stub_api.stubAddAlbum(config.album, config.album_id)
		self.stub_api.stubAddPhoto(config.album_id, 'filename0.jpg', 'filename0.jpg', 'tag',
				small_jpg+b'0')
		self.stub_api.stubAddPhoto(config.album_id, 'filename1.jpg', 'filename1.jpg', 'tag',
				small_jpg+b'1')
		self.stub_api.stubAddPhoto(config.album_id, 'filename2.jpg', 'filename2.jpg', 'tag',
				small_jpg+b'2')

		sync(config, self.flickrwrapper)

		# Verify remote files exist.
		with open('/tmp/filename0.jpg', 'rb') as f:
			self.assertEqual(f.read(), small_jpg+b'0')
		with open('/tmp/filename1.jpg', 'rb') as f:
			self.assertEqual(f.read(), small_jpg+b'1')
		with open('/tmp/filename2.jpg', 'rb') as f:
			self.assertEqual(f.read(), small_jpg+b'2')

	def testPushCleanMerge(self):
		"""Push, merge distinct local and remote content."""
		self.fs.create_file('/tmp/filename0.jpg', contents=small_jpg+b'0')
		self.fs.create_file('/tmp/filename1.jpg', contents=small_jpg+b'1')

		config = Config('albumname', '/tmp', api_key='apikey', api_secret='apisecret',
				checksum=True, push=True)

		self.stub_api.stubAddAlbum(config.album, config.album_id)
		self.stub_api.stubAddPhoto(config.album_id, 'filename2.jpg', 'filename2.jpg', 'tag',
				small_jpg+b'2')

		sync(config, self.flickrwrapper)

		self.assertEqual(sorted(self.stub_api.uploaded), sorted(['/tmp/filename0.jpg',
				'/tmp/filename1.jpg']))

	def test_push_favor_remote(self):
		"""Push, don't overwrite remote mismatched content."""
		self.fs.create_file('/tmp/filename0.jpg', contents=small_jpg+b'0')
		self.fs.create_file('/tmp/filename1.jpg', contents=small_jpg+b'1')

		config = Config('albumname', '/tmp', api_key='apikey', api_secret='apisecret', push=True)
		config.album_id = 123

		self.stub_api.stubAddAlbum(config.album, config.album_id)
		self.stub_api.stubAddPhoto(config.album_id, 'filename1.jpg', 'filename1.jpg',
				'checksum:md5=badchecksum', b'bad content')

		sync(config, self.flickrwrapper)

		self.assertEqual(self.stub_api.uploaded, ['/tmp/filename0.jpg'])

	def test_push_overwrite_remote(self):
		"""Push, overwrite remote mismatched content."""
		self.fs.create_file('/tmp/filename0.jpg', contents=small_jpg+b'0')
		self.fs.create_file('/tmp/filename1.jpg', contents=small_jpg+b'1')

		config = Config('albumname', '/tmp', api_key='apikey', api_secret='apisecret',
				checksum=True, push=True)

		self.stub_api.stubAddAlbum(config.album, config.album_id)
		self.stub_api.stubAddPhoto(config.album_id, 'filename1.jpg', 'filename1.jpg',
				'checksum:md5=badchecksum', b'bad content')

		sync(config, self.flickrwrapper)

		self.assertEqual(sorted(self.stub_api.uploaded), sorted(['/tmp/filename0.jpg',
				'/tmp/filename1.jpg']))
