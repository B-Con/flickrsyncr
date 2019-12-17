"""Logic for merging and transferring content between local and Flickr."""
import hashlib
import logging
import os

import magic

from .general import SyncError
from .general import CHECKSUM_TAG_PREFIX
from .general import CHECKSUM_TAG_PREFIX_NORMALIZED
from .config import Config
from .status import updateStatus


__all__ = ['sync']
logger = logging.getLogger(__name__)


class _Photo():
	def __repr__(self):
		return self.title

	def delete(self, config):
		pass

	def checksum(self):
		pass

	def transfer(self, config):
		pass


class LocalPhoto(_Photo):
	"""A photo on the local filesystem."""
	def __init__(self, flickrwrapper, title, path):
		"""Create an object representation of a file. Args:

		flickrwrapper - FlickrWrapper API object.
		title - The name of the file, which is the title of the photo it would upload to.
		path - The directory the file is in.
		"""
		logger.info('New local photo: title={}, path={}'.format(title, path))
		self.flickrwrapper = flickrwrapper
		self.title = title
		self.path = path

	def __eq__(self, other):
		"""Required for sorting.
		"""
		if not isinstance(other, LocalPhoto):
			return NotImplemented
		return self.title == other.title and self.path == other.path

	def __lt__(self, other):
		"""Required for sorting.
		"""
		if not isinstance(other, LocalPhoto):
			return NotImplemented
		return self.title < other.title

	def delete(self, config):
		f = os.path.join(self.path, self.title)
		updateStatus('Deleting from local: ' + f)
		if not config.dryrun:
			logger.info('Deleting from local: ' + f)
			os.remove(f)

	def _compileTags(self, config):
		# Assemble the tags to apply. The user custom tag plus the checksum tag. Convert to a
		# space-delimited string afterward.
		tags = []
		if config.tag:
			tags.append(config.tag)
		if config.checksum:
			tags.append(createChecksumTag(self.checksum()))
		return ' '.join(tags)

	# Calculate the checksum of a local file. Return it as a hex string.
	# Use MD5 as the checksum. (This isn't for security.)
	def checksum(self):
		filename = os.path.join(self.path, self.title)
		hash_ctx = hashlib.md5()
		with open(filename, 'rb') as f:
			# Read in 1 MiB chuck sizes.
			for blk in iter(lambda: f.read(2**20), b''):
				hash_ctx.update(blk)
		checksum = hash_ctx.hexdigest()
		logger.debug('Calculated checksum for photo "{}": {}'.format(self.title, checksum))
		return checksum

	def transfer(self, config):
		"""Upload the local file to Flickr.
		"""
		filename = os.path.join(self.path, self.title)

		# Sanity-check file's MIME type and only handle images (which start with "image/").
		# Read a peek of the file's content and give it to from_buffer(). Don't use
		# magic.from_file() because it isn't compatable with unit tests (it imports a C library
		# that can't be patched by pyfakefs).
		with open(filename, 'rb') as f:
			file_type = magic.from_buffer(f.read(1024), mime=True)
		if not file_type.startswith('image/'):
			updateStatus('Skipping non-image: ' + filename)
			return

		updateStatus('Uploading: ' + filename)
		if not config.dryrun:
			logger.info('Uploading {} to album_id {}'.format(filename, config.album_id))
			# TODO: Uploads are serial, add parallel?
			tags = self._compileTags(config)
			uploaded_album_id = self.flickrwrapper.upload(filename, self.title, tags,
						config.album, config.album_id)
			# It's possible Flickr will reject the content even after the MIME filter.
			if uploaded_album_id == None:
				updateStatus('...failed to upload to Flickr')
			else:
				config.album_id = uploaded_album_id


class RemotePhoto(_Photo):
	"""A Photo in a Flickr album."""
	def __init__(self, flickrwrapper, title, photo_id, tags):
		"""Create a wrapper object for a flickr photo. Args:

		flickrwrapper - FlickrWrapper API object.
		title - title of the photo
		photo_id - the Flickr ID of the photo
		tags - formatted python list (not the Flickr format of space-delimited string).
		"""
		logger.info('New remote photo: title={}, id={} tags={}'.format(title, photo_id, tags))
		self.flickrwrapper = flickrwrapper
		self.title = title
		self.photo_id = photo_id
		self.tags = tags

	def __eq__(self, other):
		"""Required for sorting.
		"""
		if not isinstance(other, RemotePhoto):
			return NotImplemented
		return self.title == other.title and self.photo_id == other.photo_id

	def __lt__(self, other):
		"""Required for sorting.
		"""
		if not isinstance(other, RemotePhoto):
			return NotImplemented
		return self.title < other.title

	def delete(self, config):
		"""Deletes the photo from flickr. Returns nothing.
		"""
		updateStatus('Deleting from album: ' + self.title)
		if not config.dryrun:
			logger.info('Deleting from album: ' + self.title)
			self.flickrwrapper.delete(photo_id=self.photo_id)

	def checksum(self):
		"""Returns the photo's checksum, retrieved from the photo's tags. Returns empty string if
		no checksum exists.
		"""
		for tag in self.tags:
			checksum = parse_checksum_tag(tag)
			if checksum:
				logger.debug('Checksum (from tags) for "{}": {}'.format(self.title, checksum))
				return checksum
		return ''

	def transfer(self, config):
		"""Downloads the photo content to the local filesystem. Output file is config.path
		with the photo title as the filename. Returns nothing.
		"""
		updateStatus('Downloading: "{}"'.format(self.title))
		if not config.dryrun:
			output_path = os.path.join(config.path, self.title)
			logger.debug('Downloading to "{}"'.format(output_path))
			photo_content = self.flickrwrapper.download(self.photo_id)
			with open(output_path, 'wb') as f:
				f.write(photo_content)


class MismatchedPhoto():
	"""Essentially a named tuple for a LocalPhoto and RemotePhoto."""
	def __init__(self, local_photo, remote_photo):
		self.local_photo = local_photo
		self.remote_photo = remote_photo

	def __repr__(self):
		return '({},{})'.format(self.local_photo, self.remote_photo)


def filterRemote(photos):
	return list(map(lambda p: p.remote_photo, photos))


def filterLocal(photos):
	return list(map(lambda p: p.local_photo, photos))


def loadRemotePhotos(config, flickrwrapper):
	"""Get the photos in the album. If album_id isn't set (because the album might be created
	later), returns an empty list.
	"""
	if not config.album_id:
		return []

	album_listing = flickrwrapper.listAlbum(config.album_id)
	# Convert the JSON responses to RemotePhoto object.
	photos = map(lambda p: RemotePhoto(flickrwrapper, p['title'], p['id'], p['tags'].split(' ')), album_listing)

	# If a tag is specified, filter on only those photos.
	if config.tag:
		tagged_photos = filter(lambda p: config.tag in p.tags, photos)
		return tagged_photos

	return photos


def loadLocalPhotos(config, flickrwrapper):
	"""Takes a Confg and FlickrWrapper and returns a list of LocalPhotos corresponding to the
	config.
	"""
	try:
		# os.listdir ordering is not guaranteed, sort it because that's probably what users expect.
		dir_listing = sorted(os.listdir(config.path))
	except FileNotFoundError:
		raise SyncError('Local path not found: ' + config.path)

	# Filter only the files.
	# TODO: Recursively traverse sub-dirs?
	local_files = list(filter(lambda f: os.path.isfile(os.path.join(config.path, f)), dir_listing))
	logger.info('Local files: ' + str(local_files))

	# Wrap each file in a LocalPhoto.
	photos = map(lambda f: LocalPhoto(flickrwrapper, f, config.path), local_files)
	return photos


def createChecksumTag(checksum):
	return CHECKSUM_TAG_PREFIX + checksum


def parse_checksum_tag(tag):
	checksum = ''
	if tag.startswith(CHECKSUM_TAG_PREFIX):
		checksum = tag[len(CHECKSUM_TAG_PREFIX):]
	return checksum


def deletePhotos(config, photos):
	for p in photos:
		p.delete(config)


def transferPhotos(config, photos):
	"""Transfer a list of photos. Skip failures and raise an exception at the end.
	"""
	errors = []
	for p in photos:
		try:
			p.transfer(config)
		except SyncError as err:
			errors.append(err)
	if errors:
		raise SyncError(str(errors))


def diffPhotos(local_photos, remote_photos):
	"""Compares a set of LocalPhotos to a set of RemotePhotos and returns the sets that are unique
	and mismatched.

	Args:
	  local_photos  - dict of LocalPhotos, title->LocalPhoto
	  remote_photos - list of RemotePhotos

	Returns:
	  A tuple (local_only, remote_only, mismatched), where:
		  local_only  - photos in local_photos and not in remote_photos
		  remote_only - photos in remote_photos and not in local_photos
		  mismatched  - tuple of (LocalPhoto, RemotePhoto) that refer to the same photo were the
		                checksums don't match
	"""
	# Build a list of files exclusive to remote and to local.
	#   * Remove contents of "remote" from "local".
	#   * Anything not in local is exclusive to remote.
	#   * Anything not removed from local is exclusive to local.
	#   * Anything in both but with a mismatched checksum is processed separately. (RemotePhoto
	#     can be cast to LocalPhoto, but not the other way around.)
	# Convert local photos to a dict for random access and use it as the set of local only photos.
	# The dict keeps the original photo objects as the values.
	local_only = {p.title : p for p in local_photos}
	remote_only = []
	mismatched = []
	for p in remote_photos:
		if p.title in local_only:
			remote_checksum = p.checksum()
			local_checksum = local_only[p.title].checksum()
			if remote_checksum != local_checksum:
				logger.info('Mismatched checksums on "{}": local={}, remote={}'.format(
						p.title, local_checksum, remote_checksum))
				mismatched.append(MismatchedPhoto(local_only[p.title], p))
			local_only.pop(p.title)
		else:
			remote_only.append(p)
	# The remaining keys are what's unique to local. Flatten it back into a list.
	local_only = list(local_only.values())

	logger.info('Local only content: ' + str(local_only))
	logger.info('Remote only content: ' + str(remote_only))
	logger.info('Mismatched checksums: ' + str(mismatched))

	return (local_only, remote_only, mismatched)


def sync(config, flickrwrapper):
	"""Synchronizes content from the source to the destination, using the necessary upload,
	download, and delete operations per the settings in config.

	Returns nothing. Raises a SyncError on failure.
	"""
	logger.info(str(config))
	# Validate the config first before acting on data. Inconsistent config could damage data.
	config.validate()

	local_photos = loadLocalPhotos(config, flickrwrapper)
	remote_photos = loadRemotePhotos(config, flickrwrapper)

	local_only, remote_only, mismatched = diffPhotos(local_photos, remote_photos)

	# Transfer and remove files to sync appropraitely per config. The diff of content overlapping
	# between local, remote, and mismatched has been calculated. Three things that must happen:
	# 1) Transfer the content exclusive to the source.
	# 2) If checksum matching enabled, overwrite mismatching destination content from the source.
	# 3) If sync is enabled, remove content exclusive to the destination.
	if config.push:
		transferPhotos(config, local_only)
		if config.checksum:
			deletePhotos(config, filterRemote(mismatched))
			transferPhotos(config, filterLocal(mismatched))
		if config.sync:
			deletePhotos(config, remote_only)

	if config.pull:
		transferPhotos(config, remote_only)
		if config.checksum:
			deletePhotos(config, filterLocal(mismatched))
			transferPhotos(config, filterRemote(mismatched))
		if config.sync:
			deletePhotos(config, local_only)
