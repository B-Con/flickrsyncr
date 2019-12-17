"""Wrapper for the Flickr API."""
import logging
import urllib

import flickrapi

from .general import SyncError
from .status import updateStatus


__all__ = ['getFlickrAPI', 'FlickrWrapper']
logger = logging.getLogger(__name__)


# TODO: Currently only supports one user, we would have to differentiate user tokens in storage.
def getFlickrAPI(config):
	"""Obtains the Flickr API interface and loads local OAuth tokens if necessary.
	Args
		config: A Config object, used to find the local OAuth tokens.

	Returns
		FlickrWrapper
	"""
	logger.info('Obtaining Flickr API, checking credentials in: "{}"'.format(config.dir_))
	flickr = flickrapi.FlickrAPI(config.api_key, config.api_secret,
			token_cache_location=config.dir_, format='parsed-json')

	if not flickr.token_valid(perms='delete'):
		logger.info('No OAuth token for user')
		updateStatus('No existing valid OAuth tokens in config path {}'.format(config.dir_))
		flickr.authenticate_console(perms='delete')

	token = flickr.auth.oauth.checkToken()
	if token['stat'] != 'ok':
		raise SyncError("Couldn't get an OAuth token")

	user_id = token['oauth']['user']['nsid']
	return FlickrWrapper(flickr, user_id)


class FlickrWrapper():
	"""Wraps the FlickerAPI for the commonly used functions."""
	def __init__(self, flickr, user_id):
		self.flickr = flickr
		self.user_id = user_id

	def getAlbumID(self, album_name):
		"""Get album's unique ID. Must iterate over pages of albums to find it.
		"""
		# Pages are indexed from 1. Total page count is read from the API response.
		page_num = 1
		page_count = 1
		while page_num <= page_count:
			page = self.flickr.photosets.getList(user_id=self.user_id, page=page_num)
			page_count = page['photosets']['pages']
			page_num += 1
			for album in page['photosets']['photoset']:
				if album['title']['_content'] == album_name:
					return album['id']
		logger.debug('No album with name {}. It can be created later.'.format(album_name))
		return None

	def createAlbum(self, album_name, photo_id):
		"""Create a Flickr album. A default photo is required.
		"""
		resp = self.flickr.photosets.create(title=album_name, primary_photo_id=photo_id)
		logger.info('Creating album: ' + str(resp))
		if resp['stat'] != 'ok':
			raise SyncError('Could not create album "{}", err={}'.format(album_name, resp['stat']))
		return resp['photoset']['id']

	def listAlbum(self, album_id):
		"""List the photos in an album.
		"""
		# Download all the album pages. Pages are indexed from 1. Update the
		# page count once we make an API request.
		# TODO: use the "for p in flickr.walk_set(config.album_id, per_page=500)" API?
		# See https://stuvel.eu/flickrapi-doc/7-util.html#walking-through-all-photos-in-a-set .
		page_num = 1
		page_count = 1
		results = []
		while page_num <= page_count:
			page = self.flickr.photosets.getPhotos(photoset_id=album_id, user_id=self.user_id,
					page=page_num, extras='tags')
			page_count = page['photoset']['pages']
			page_num += 1
			logger.debug('Album {} listing: {}'.format(album_id, page))
			results += page['photoset']['photo']
		return results

	def delete(self, photo_id):
		"""Delete a photo from flickr. Returns nothing, raises exception for error.
		"""
		self.flickr.photos.delete(photo_id=photo_id)

	def upload(self, filename, title, tags, album_name=None, album_id=None):
		"""Upload a file to an album id. Create the album named album_name the id doesn't exist. Returns the used album id, or None if the upload didn't complete. Uploads must be added
		to an album.
		"""
		# The upload API only supports XML responses, so use "etree".
		logger.info('Uploading photo: ' + filename)
		try:
			resp = self.flickr.upload(filename, title=title, tags=tags, format='etree',
					is_public=1, is_friend=0, is_family=0)
		except flickrapi.exceptions.FlickrError as e:
			if e.code == 5:
				logger.info('File {} is not an accepted file type, skipping'.format(filename))
			return None

		if resp.attrib['stat'] != 'ok':
			raise SyncError('Could not upload photo "{}", err={}'.format(filename,
					resp.attrib['stat']))
		photo_id = resp.find('photoid').text

		# Add the new photo to the destination album. Create the album if it doesn't exist
		# yet. It may not exist because albums can't be empty (and they are automatically removed
		# when emptied), so a photo must be uploaded first. Creating the album and adding a cover
		# photo adds that photo to the album.
		try:
			self.flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
		except flickrapi.exceptions.FlickrError as e:
			# Code "1" means "album ID not found".
			if e.code == 1:
				msg = "Album ID {} doesn't exist, creating it".format(album_id)
				logger.debug(msg)
				updateStatus(msg)
				album_id = self.createAlbum(album_name, photo_id)
		return album_id

	def download(self, photo_id):
		"""Downloads a photo and returns it as raw bytes.
		"""
		# getSizes() fetches the resolutions available for the photo, including their URLs. Use
		# the resolution named 'Original' to get back what upload() put in. (AFAIK it's always
		# available.)
		sizes = self.flickr.photos.getSizes(photo_id=photo_id)
		logger.debug('Resolutions available for {}: {}'.format(photo_id, sizes))
		for s in sizes['sizes']['size']:
			if s['label'] == 'Original':
				logger.info('Downloading: ' + photo_id)
				# Property 'source' is the URL for the image data, property 'url' is just a
				# web page that shows it.
				r = urllib.request.urlopen(s['source'])
				return r.read()
		raise SyncError('Could not download image "{}" because Flickr provided no URL for ' +
					'the "Original" image resolution.'.format(photo_id))
