from setuptools import setup


with open('README.md', encoding='utf-8') as f:
    readme = f.read()

with open('LICENSE', encoding='utf-8') as f:
    license = f.read()

with open('requirements.txt') as f:
    # Basic functionality requires all the listed dependencies.
    install_req = f.read().split()

setup(
    name = 'flickrsyncr',
    version = '0.2.1',  # Keep in sync with flickrsyncr.VERSION.
    packages = ['flickrsyncr'],
    description = 'Syncs photos between local filesystem and Flickr album',
    long_description = readme,
    long_description_content_type = 'text/markdown',
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
