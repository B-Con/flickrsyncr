from setuptools import setup
import flickrsyncr


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name = 'flickrsyncr',
    version = flickrsyncr.__version__,
    packages = ['flickrsyncr'],
    description = 'Syncs photos between local filesystem and Flickr album',
    long_description = readme,
    author = 'Brad Conte',
    author_email = 'brad@bradconte.com',
    url = 'https://github.com/B-Con/flickrsyncr',
    license = license,
    scripts = ['bin/flickrsyncr'],
    keywords='flickr sync upload download backup photo album',
)
