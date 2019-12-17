import unittest

# Testing support.
from test.stub_flickrapi import StubFlickrAPI
# Officially exported names.
from flickrsyncr import Config
from flickrsyncr import flickrwrapper


class TestFlickrWrapper(unittest.TestCase):
	"""Exercise the methods in flickrwrapper.
	"""
	def setUp(self):
		self.config = Config('albumname', '/my/dir', push=True, api_key='apikey',
				api_secret='apisecret', tag='tag2')
		self.stub_api = StubFlickrAPI()
		self.apiwrapper = flickrwrapper.FlickrWrapper(self.stub_api, 'userid')
		# Patch urlopen in module flickrwrapper.
		flickrwrapper.urllib.request.urlopen = self.stub_api.stubURLOpenner()

	def testGetAlbumID(self):
		self.stub_api.stubAddAlbum('albumname', 123)
		self.assertEqual(self.apiwrapper.getAlbumID('albumname'), 123)

	def testCreateAlbum(self):
		self.assertNotEqual(self.apiwrapper.createAlbum('albumname', 'userid'), 0)

	def testListAlbum(self):
		"""Seed the stub with album and photos and list the album.
		"""
		self.stub_api.stubAddAlbum('albumname', 123)
		self.stub_api.stubAddPhoto(123, 'Photo 1', '1111', 'tag1 tag2 tag3', b'')
		self.stub_api.stubAddPhoto(123, 'Photo 2', '2222', 'tag1', b'')
		self.stub_api.stubAddPhoto(123, 'Photo 3', '3333', 'tag2 tag3', b'')
		self.stub_api.stubAddPhoto(123, 'Photo 4', '4444', '', b'')

		want = [
			{
				'title': 'Photo 1',
				'id': '1111',
				'tags': 'tag1 tag2 tag3',
			},
			{
				'title': 'Photo 2',
				'id': '2222',
				'tags': 'tag1',
			},
			{
				'title': 'Photo 3',
				'id': '3333',
				'tags': 'tag2 tag3',
			},
			{
				'title': 'Photo 4',
				'id': '4444',
				'tags': '',
			},
		]
		got = self.apiwrapper.listAlbum(123)
		sort_key = lambda p: p['title']
		self.assertEqual(sorted(got, key=sort_key), sorted(want, key=sort_key))

	def testUploadExistingAlbum(self):
		"""Upload to an existing album. Errors raise exceptions.
		"""
		self.apiwrapper.upload('/tmp/filename1', 'Photo Title 1', 'tag1 tag2', album_name='albumname', album_id=123)
		self.assertEqual(self.stub_api.uploaded, ['/tmp/filename1'])

	def testUploadNonexistingAlbum(self):
		"""Uplaod to no album, so one is created. Errors raise exceptions.
		"""
		self.apiwrapper.upload('/tmp/filename1', 'Photo Title 1', 'tag1 tag2', album_name='albumname')
		self.assertEqual(self.stub_api.uploaded, ['/tmp/filename1'])

	def testDownload(self):
		"""Seed the stub with file content and download it.
		"""
		self.stub_api.stubAddAlbum('albumname', 123)
		self.stub_api.stubAddPhoto(123, 'Photo 1', 'photoid123', 'tag1 tag2 tag3', b'filecontent')

		self.assertEqual(self.apiwrapper.download(photo_id='photoid123'), b'filecontent')
