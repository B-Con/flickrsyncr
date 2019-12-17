import random
from xml.etree import ElementTree

import flickrapi


_all__ = ['StubFlickrAPI', 'small_jpg']
# Small, valid JPEG file. Useful for passing content type validation.
small_jpg = b'\xff\xd8\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9'


class StubFlickrAPI():
	"""Stub to replace flickrapi.FlickrAPI. Returns stub values for the JSON version of the API,
	eg. if the API is invoked like:

	    flickrapi.FlickrAPI(..., format='parsed-json')

	Library docs: https://stuvel.eu/flickrapi-doc/
	Flickr API: https://www.flickr.com/services/api/
	"""

	####################
	# Stubbed attributes
	####################

	class StubPhotosets():
		"""Stub for attribute flickrapi.FlickrAPI().photosets. Populate the data it serves with
		stubAddAlbum().
		"""
		def __init__(self):
			self.albums = []
			self.photos = {}

		def getList(self, *args, page='', **kwargs):
			"""Hard-coded results pages for listing albums. Result indexed by results page number.
			"""
			return self.albums[page-1]

		def create(self, *args, **kwargs):
			"""Create an album, always respond OK with a random album ID. Return a random album ID. Does not actually populate the stub data store, use stubAdd Album for that.
			"""
			new_id = random.randint(1000, 10000)
			result = {
				'stat': 'ok',
				'photoset': {
					'id': new_id,
				},
			}
			return result

		def getPhotos(self, *args, photoset_id='', page='', **kwargs):
			"""Hard-coded results for an album list. Result indexed by album ID and page.
			"""
			return self.photos[photoset_id][page-1]

		def addPhoto(self, photoset_id=None, **kwargs):
			for a in self.albums:
				if a['photosets']['photoset'][0]['id']:
					return
			raise flickrapi.exceptions.FlickrError("album doesn't exist", code=1)

	class StubPhotos():
		"""Stub for attribute flickrapi.FlickrAPI().photos. Populate the content it serves with
		stubAddPhoto().
		"""
		def __init__(self):
			self.sizes = {}

		def getSizes(self, photo_id=''):
			return self.sizes[photo_id]

		def delete(self, photo_id=''):
			if not photo_id in self.sizes:
				raise flickrapi.exceptions.FlickrError("photo doesn't exist", code=1)

	def __init__(self):
		self.photosets = self.StubPhotosets()
		self.photos = self.StubPhotos()
		self.photo_contents = {}
		self.uploaded = []

	def upload(self, filename, **kwargs):
		"""Create an album, always respond OK with a random album ID. Return a random album ID. Does not actually populate the stub data store, use stubAdd Album for that. Logs the
		uploaded filenames in self.uploaded as a "spy" stub.
		"""
		self.uploaded.append(filename)
		new_id = random.randint(1000, 10000)

		rsp = ElementTree.Element('rsp')
		rsp.attrib['stat'] = 'ok'
		photoid = ElementTree.Element('photoid')
		photoid.text = new_id
		rsp.append(photoid)
		return rsp

	#############################
	# Helper functions, not stubs
	#############################

	def stubAddAlbum(self, album_name, album_id):
		"""Seed the stub with an album. It will appear in stubbed album-related APIs.
		"""
		new_page = {
			'photosets': {
				'pages': 0,  # Overwridden later.
				'photoset': [
					{
						'title': {
							'_content': album_name,
						},
						'id': album_id,
					},
				],
			},
		}
		self.photosets.albums.append(new_page)

		# Init the album's content.
		self.photosets.photos[album_id] = []

		# Update the number of pages in the album.
		for a in self.photosets.albums:
			a['photosets']['pages'] = len(self.photosets.albums)

	def stubAddPhoto(self, album_id, title, photo_id, tags, content):
		"""Seed the stub with a photo. It will appear in stubbed photo-related APIs.
		"""
		new_page = {
			'photoset': {
				'pages': 0,  # Overwridden later.
				'photo': [
					{
						'title': title,
						'id': photo_id,
						'tags': tags,
					},
				],
			},
		}
		self.photosets.photos[album_id].append(new_page)

		# Update the number of pages of photos.
		for p in self.photosets.photos[album_id]:
			p['photoset']['pages'] = len(self.photosets.photos[album_id])

		# Create a URL responses for the photo.
		self.photos.sizes[photo_id] = {
			'sizes': {
				'size': [
					{
						'label': 'Original',
						'source': 'http://domain.com/' + photo_id,
					},
					{
						'label': 'Other',
						'source': 'http://domain.com/other-' + photo_id,
					},
				],
			},
		}

		# Create the URL map.
		self.photo_contents['http://domain.com/' + photo_id] = content

	def stubURLOpenner(self):
		"""Returns an object implementing read(url=) to be patched over urllib. Reads for the URL
		return the photos stored at that URL, added using stubAddPhoto().

		Sample usage:
			stub_api = StubApi()
			stub_api.AddPhoto(..., photo_id=photoid, ...)
		    urllib.request.urlopen = stub_api.stubURLOpenner('http://domain.com/' + photoid)
		"""
		class Reader():
			def __init__(self, content):
				self.content = content
			def read(self):
				return self.content

		def stubURLOpen(url=''):
			return Reader(self.photo_contents[url])

		return stubURLOpen
