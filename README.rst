===========
FlickrSyncr
===========

A Python library and command-line applications for syncing photos between a local directory and a Flickr album.

Photos are matched by local filename and Flickr photo title with the option of also comparing the local and Flickr photo checksums. Mismatching content is synced in the direction the user specifies.

    * https://github.com/B-Con/flickrsyncr
    * https://bradconte.com/flickrsyncr
    * https://pypi.python.org/pypi/flickrsyncr

Setup
=====

1. Obtain a Flickr API KEY. Starting point: <https://www.flickr.com/services/apps/create/apply>.

2.     Save the API key and secret in a config file (unless you will provide it on the cmd-line or in the ``Settings()`` object).

       *     The config file at ``~/.config/flickrsyncr/config.conf`` will used by default unless an alternative path is specified via ``--config_dir``. Sample config file content (there is also one in ``tests/config/config.conf``)::

                 [DEFAULT]
                 api_key = 0123456789abcdef0123456789abcdef
                 api_secret = 0123456789abcdef

    * Multiple API key/secret pairs can be stored under different profile names. The ``DEFAULT`` profile will be used by default unless an alternative profile name is specified via ``--config_profile``.

3.    On the first run, human involvement is necessary to authorize the app for Flickr OAuth access to the Flickr account. The app will provide a URL to visit in a web browser. Login to the Flickr account you want to associate the app with and then visit the displayed URL to grant the app permission.

      ``delete`` permissions are necessary for syncing and removing content.

      OAuth permissions are still checked and obtained in ``dryrun`` mode.

Usage
=====

Command-line application
------------------------

Basics:

* Only the local ``--path`` and Flickr ``--album`` are required.
* One of ``--push`` or ``--pull`` is required.
* Use ``--help`` to list all options.

Examples:

* Force the Flickr album contents to exactly match local dir based only on file name::

    $ flickrsyncr --album=albumname --path=/my/dir --push --sync

* Force the Flickr album contents to exactly match local dir based on file name and checksum::

    $ flickrsyncr --album=albumname --path=/my/dir --push --sync --checksum

* Add local files into a Flickr album::

    $ flickrsyncr --album=albumname --path=/my/dir --push

* Add local files into a Flickr album and tag them all::

    $ flickrsyncr --album=albumname --path=/my/dir --push --tag=mycustomtag

* See what would change if a Flickr album were added to a local directory::

    $ flickrsyncr --album=albumname --path=/my/dir --pull --dryrun

Library
-------

Objects of interest:

* ``flickrsyncr.Settings`` - A class containing all necessary settings. Only the
* ``flickrsyncr.sync`` - Main execution function. Takes a ``Settings()`` as the only argument.
* ``flickrsyncr.SyncError`` - Generic exception thrown by the pacakge on fatal errors.

Create a ``Settings()`` with the required settings in the constructor and pass it to ``sync()``.

The cmd-line tool is basically just a wrapper to convert cmd-line arguments into a ``Settings()`` and then calls ``sync()``.

See the cmd-line section for examples, the cmd-line arguments and ``Settings()`` arguments share the same names (except for the ``--`` hyphen prefix).

Requirements
============

Python Packages
---------------

* Python3
* Pip
* FlickrApi
* ConfigParser
* SetupTools

Flickr Access
-------------

* Flickr account
* Flickr API key/secret pair

Install
=======

    $ pip install flickrsyncr

This installs both the library and the cmd-line script.

References
==========

* https://stuvel.eu/flickrapi
* https://www.flickr.com/services/api/

Inner Workings
==============

See the cmd-line prompt ``--help`` for the most detail on the settings/arguments.

Local state
-----------

* ``~/.config/flickrsyncr/``, containing a user-created ``config.conf`` (if applicable) and ``oauth-tokens.sqlite`` (managed by the flickrapi library).

Syncing
-------

* It builds a list of Flickr photos, filtered by the value of ``tag`` if it's specified.

* It builds a list of local files.

* Flickr photos and local files are matched by compare the local filename and the Flickr photo title.

* A list of unique photos is made for local and for Flickr.

* If ``checksum`` is specified, a list of photos with mismatched checksums is compiled. Flickr photos without checksums will always mismatch.

*    For ``push``:

     * unique local photos are uploaded.
     * if ``checksum`` is specified, mismatched photos are deleted from Flickr and then uploaded.
     * if ``sync`` is specified, all unique Flickr photos are deleted.

*    For ``pull``:

     * unique remote photos are downloaded.
     * if ``checksum`` is specified, mismatched photos are deleted from local path and then downloaded.
     * if ``sync`` is specified, all unique local photos are deleted.

Uploads
-------

* If ``tag`` is specified, uploaded photos have the tag value added.
* If ``checksum`` is specified, the file's checksum is stored on Flickr as a tag.
* The photo's local file name is used as the Flickr photo title.
* The album is created if it doesn't exist, with the banner of the first uploaded picture.

Downloads
---------

* If ``tag`` is specified, the app won't notice any Flickr photos without the tag value.
* The Flickr photo title is used as the local file name.

Edge-Cases & Gotchas
====================

* Flickr's API calls an "album" a "photoset". They're the same thing.
* Flickr automatically deletes an album when it has no pictures. During a sync, if all the photos are deleted before more are uploaded then the album will be deleted by Flickr and re-created by this script. You will lose your album metadata tweaks, sorry.
* To delete a Flickr album and it's contents, ``--push`` and empty directory with the album name.
* Tag values are not added retroactively (and cannot be by the app). ex: ``--push`` followed by ``--push --tag=mytag`` will cause the entire album to be re-uploaded because the initial photos are invisible when ``--tag=mytag`` was specified.
* Checksums are not added retroactively (and cannot be by the app). ex: ``--push`` followed by ``--push --checksum`` will cause the entire album to be deleted and re-uploaded because the initial push had no checksum and no checksum mismatches with the real checksum in the second step.
