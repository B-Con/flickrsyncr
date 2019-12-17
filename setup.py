from setuptools import setup
#from flickrsyncr import VERSION

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('requirements.txt') as f:
    # Basic functionality requires all the listed dependencies.
    install_req = f.read().split()

setup(
    name = 'flickrsyncr',
    version = '0.1.7',
    packages = ['flickrsyncr'],
    description = 'Syncs photos between local filesystem and Flickr album',
    long_description = readme,
    author = 'Brad Conte',
    author_email = 'brad@bradconte.com',
    url = 'https://github.com/B-Con/flickrsyncr',
    license = license,
    keywords = 'flickr sync upload download backup photo album photo pic',
    install_requires = install_req,
    entry_points = {
        "console_scripts": [
            "flickrsyncr=flickrsyncr:cli",
        ]
    },
    test_suite = 'nose.collector',
    tests_require = ['nose'],
)
