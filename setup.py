# -*- coding: utf-8 -*-
from distutils.core import setup

VERSION = '0.1'
URL = 'https://github.com/operasoftware/mpns-client'
DOWNLOAD_URL = URL + '/tarball/' + VERSION

setup(
    name='mpns-client',
    packages=['mpns'],
    version=VERSION,
    description='Microsoft Push Notification Service client',
    author=u'Piotr Śliwka',
    author_email='psliwka@opera.com',
    url=URL,
    download_url=DOWNLOAD_URL,
    keywords=['mpns', 'twisted'],
    license='MIT',
    install_requires=['Twisted>=15.0.0']
)
