import flickrapi
import hashlib
import logging
import os
import urllib
from flickrsyncr.general import logger
from flickrsyncr.general import SyncError
from flickrsyncr.settings import Settings
from flickrsyncr.general import CHECKSUM_TAG_PREFIX
from flickrsyncr.general import CHECKSUM_TAG_PREFIX_NORMALIZED


class Photo():
    def __repr__(self):
        return self.title

    def delete(self, flickr, settings):
        pass

    def getChecksum(self):
        pass

    def transfer(self, flickr, settings):
        pass


class LocalPhoto(Photo):
    def __init__(self, title, path):
        logger.info('New local photo: title={}, path={}'.format(title, path))
        self.title = title
        self.path = path

    def delete(self, flickr, settings):
        f = os.path.join(self.path, self.title)
        msg = 'Deleting from local: ' + f
        logger.info(msg)
        print(msg)
        if not settings.dryrun:
            os.remove(f)

    # Calculate the checksum of a local file. Return it as a hex string.
    # Use MD5 as the checksum. (This isn't for security.)
    def getChecksum(self):
        filename = os.path.join(self.path, self.title)
        hash_ctx = hashlib.md5()
        with open(filename, 'rb') as f:
            # Read in 1 MiB chuck sizes.
            for blk in iter(lambda: f.read(2**20), b''):
                hash_ctx.update(blk)
        checksum = hash_ctx.hexdigest()
        logger.debug('Calculated checksum for photo "{}": {}'.format(self.title, checksum))
        return checksum

    def compileTags(self, settings):
        # Assemble the tags to apply. The user custom tag plus the checksum tag. Convert to a
        # space-delimited string afterward.
        tags = []
        if settings.tag:
            tags.append(settings.tag)
        if settings.checksum:
            tags.append(createChecksumTag(self.getChecksum()))
        return ' '.join(tags)

    def transfer(self, flickr, settings):
        filename = os.path.join(self.path, self.title)
        msg = 'Uploading to album: ' + filename
        logger.info(msg)
        print(msg)
        if not settings.dryrun:
            # The upload API only supports XML responses.
            # TODO: Upload is serial. Add parallel uploads?
            tags = self.compileTags(settings)
            resp = flickr.upload(filename, title=self.title, format='etree', tags=tags,
                    is_public=0, is_friend=0, is_family=0)
            photo_id = resp.find('photoid').text
            logger.info('Uploaded photo ID: ' + photo_id)

            # Adds the new photo to the destination album. Create the album if it doesn't exist
            # yet. We have to do it after an upload because albums can't be empty so we need a
            # photo to put in it.
            if settings.album_id == None:
                # Adds the photo_id to the album (as the cover photo).
                createAlbum(flickr, settings, photo_id)
            else:
                flickr.photosets.addPhoto(photoset_id=settings.album_id, photo_id=photo_id)


class RemotePhoto(Photo):
    def __init__(self, title, id, tags):
        logger.info('New remote photo: title={}, id={} tags={}'.format(title, id, tags))
        self.title = title
        self.id = id
        self.tags = tags

    def delete(self, flickr, settings):
        msg = 'Deleting from album: ' + self.title
        logger.info(msg)
        print(msg)
        if not settings.dryrun:
            flickr.photos.delete(photo_id=self.id)

    # The checksum is stored on a Flickr photo as a tag with a fixed prefix. An empty checksum
    # can't match a valid one.
    def getChecksum(self):
        for tag in self.tags:
            checksum = parseChecksumTag(tag)
            if checksum:
                logger.debug('Found checksum for photo "{}": {}'.format(self.title, checksum))
                return checksum
        return ''

    def transfer(self, flickr, settings):
        # getSizes() is the API for info for each resolution available for the photo, including
        # its URL. Use the 'Original' size.
        sizes = flickr.photos.getSizes(photo_id=self.id)
        logger.debug(str(sizes))
        found_url = False
        for s in sizes['sizes']['size']:
            if s['label'] == 'Original':
                found_url= True
                msg = 'Downloading to local: ' + self.title
                print(msg)
                logger.info(msg)
                if not settings.dryrun:
                    # Property 'source' is the URL for the actual image, 'url' is just a web page.
                    r = urllib.request.urlopen(s['source'])
                    with open(os.path.join(settings.path, self.title), 'wb') as f:
                        f.write(r.read())
        if not found_url:
            raise SyncError('Could not download image "{}" because Flickr provided no URL for ' +
                    'the "Original" image resolution.'.format(self.title))


# Basically just tuple namespace, but could be implemented to inherit from Class Photo and wrap
# the functionality of the Photos it stores.
class MismatchedPhoto():
    def __init__(self, local_photo, remote_photo):
        self.remote_photo = remote_photo
        self.local_photo = local_photo

    def __repr__(self):
        return str(self.local_photo) + '|' + str(self.remote_photo)


def getFlickrApi(settings):
    flickr = flickrapi.FlickrAPI(settings.api_key, settings.api_secret, format='parsed-json')
    token = flickr.auth.oauth.checkToken()

    if token['stat'] != 'ok':
        logger.debug('No OAuth token for user')
        print("We need an OAuth token. A browser window is opening in which " +
              "you can authorize the app to access your Flickr account...")
        flickr.authenticate_via_browser(perms='delete')
        print("...OAuth redirect done.")
        token = flickr.auth.oauth.checkToken()

        if token['stat'] != 'ok':
            raise SyncError("Couldn't get an OAuth token")

    user_id = token['oauth']['user']['nsid']
    return flickr, user_id


# Get the unique ID of an album. The returned list is the list of all albums in pages of 500 max
# per page, indexed from 1. Update the page count once we get it in an API response.
# Can't create the album here because Flickr doesn't allow for empty albums and requires a
# photo_id for the album cover, so wait until the first photo has been uploaded then create the
# album.
def getAlbumID(flickr, settings):
    page_num = 1
    page_count = 1
    while page_num <= page_count:
        page = flickr.photosets.getList(user_id=settings.user_id, page=page_num)
        page_count = page['photosets']['pages']
        page_num += 1

        for album in page['photosets']['photoset']:
            if album['title']['_content'] == settings.album:
                    return album['id']
    logger.debug('No album with that name exists. It will be created later.')
    return None


# Create a Flickr album. A default photo is required.
def createAlbum(flickr, settings, photo_id):
    resp = flickr.photosets.create(title=settings.album, primary_photo_id=photo_id)
    logger.info('Create album: ' + str(resp))
    print('Creating album: "%s"' % settings.album)
    if resp['stat'] != 'ok':
        raise SyncError('Could not create album "{}", err={}'.format(settings.album, resp['stat']))
    settings.album_id = resp['photoset']['id']


# Get the photos in an album. The returned list is the list of all photos in the album in pages of
# 500 max per page, indexed from 1.  Update the total page count once we get it in an API response.
def getRemotePhotos(flickr, settings):
    remote_photos = []

    # If the remote album doesn't exist yet, short-circuit.
    if not settings.album_id:
        return remote_photos

    # Download all the album pages. Pages are indexed from 1. Update the
    # page count once we make an API request.
    page_num = 1
    page_count = 1
    while page_num <= page_count:
        page = flickr.photosets.getPhotos(photoset_id=settings.album_id, user_id=settings.user_id,
                page=page_num, extras='tags')
        page_count = page['photoset']['pages']
        page_num += 1

        logger.debug('Album listing: ' + str(page))
        photo_page = page['photoset']['photo']

        # Convert the parsed JSON to a RemotePhoto object.
        photos = map(lambda p: RemotePhoto(p['title'], p['id'], p['tags'].split(' ')), photo_page)

        # If a tag was specified, only process photos with it.
        if settings.tag:
            tagged_photos = filter(lambda p: settings.tag in p.tags, photos)
            remote_photos.extend(tagged_photos)
        else:
            remote_photos.extend(photos)

    return remote_photos


def getLocalPhotos(settings):
    try:
        # os.listdir ordering is not garuenteed, sort it because that's probably what users expect.
        dir_list = sorted(os.listdir(settings.path))
    except FileNotFoundError:
        raise SyncError('Local path not found: ' + settings.path)

    # Only keep files, ignore other types (eg, directories).
    # TODO: Also filter files based on file type that's an image?
    local_files = list(filter(lambda f: os.path.isfile(os.path.join(settings.path, f)), dir_list))
    logger.info('Local files: ' + str(local_files))

    # Turn file list into LocalPhoto objects.
    photos = map(lambda f: LocalPhoto(f, settings.path), local_files)

    return photos


def createChecksumTag(checksum):
    return CHECKSUM_TAG_PREFIX + checksum


def parseChecksumTag(tag):
    checksum = ''
    if tag.startswith(CHECKSUM_TAG_PREFIX_NORMALIZED ):
        checksum = tag[len(CHECKSUM_TAG_PREFIX_NORMALIZED ):]
    return checksum


def deletePhotos(flickr, settings, photos):
    for p in photos:
        p.delete(flickr, settings)


def getRemoteMismatched(photos):
    return list(map(lambda p: p.remote_photo, photos))


def getLocalMismatched(photos):
    return list(map(lambda p: p.local_photo, photos))


# Transfer the photos. Compile a list of failed images and raise the exception at the end.
def transferPhotos(flickr, settings, photos):
    errors = []
    for p in photos:
        try:
            p.transfer(flickr, settings)
        except SyncError as err:
            errors.append(err)
    if errors:
        raise SyncError(str(errors))


# local_photos - local photos, dict {title : LocalPhoto}
# remote_photos - remote photos, list [RemotePhoto]
# local_only - output of photos only in local, list [LocalPhoto]
# remote_only - output of photos only in remote, list [RemotePhoto]
# mismatched - output of photos with mismatching checksums, list [MismatchedPhoto]
def getPhotosetDifferences(local_photos, remote_photos, settings):
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
            # Make a list of mismatched photos, tracking both the local and the remote version.
            if settings.checksum:
                remote_checksum = p.getChecksum()
                local_checksum = local_only[p.title].getChecksum()
                if remote_checksum != local_checksum:
                    logger.info('Mismatched checksums on "%s": local=%s, remote=%s' %
                            (p.title, local_checksum, remote_checksum))
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


def sync(settings):
    """Uses the provided "settings" to upload, download, and delete files as appropriate.
    """
    logger.info(str(settings))
    settings.validate()

    flickr, settings.user_id = getFlickrApi(settings)
    settings.album_id = getAlbumID(flickr, settings)

    local_photos = getLocalPhotos(settings)
    remote_photos = getRemotePhotos(flickr, settings)

    local_only, remote_only, mismatched = getPhotosetDifferences(local_photos, remote_photos,
            settings)

    # Push, pull, and delete files. Delete checksum mismatches in the destination first.
    if settings.push:
        deletePhotos(flickr, settings, getRemoteMismatched(mismatched))
        transferPhotos(flickr, settings, local_only + getLocalMismatched(mismatched))
        if settings.sync:
            deletePhotos(flickr, settings, remote_only)

    if settings.pull:
        deletePhotos(flickr, settings, getLocalMismatched(mismatched))
        transferPhotos(flickr, settings, remote_only + getRemoteMismatched(mismatched))
        if settings.sync:
            deletePhotos(flickr, settings, local_only)

    return
