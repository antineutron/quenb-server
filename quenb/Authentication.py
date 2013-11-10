#!/usr/bin/env python

from cork import Cork
from cork.sqlite_backend import SQLiteBackend
from os.path import isdir, isfile
from os import makedirs
from datetime import datetime

def getAAA(userdb_dir):
    """
    Gets an authentication object for use with cork/bottle.
    """

    # Create default json files for users if not present
    if not isdir(userdb_dir):
        makedirs(userdb_dir)

    if not isfile(userdb_dir+'/register.json'):
        with open(userdb_dir+'/register.json', 'w') as f:
            f.write('{}')

    if not isfile(userdb_dir+'/users.json'):
        with open(userdb_dir+'/users.json', 'w') as f:
            now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
            f.write('{"admin": {"hash": "cLzRnzbEwehP6ZzTREh3A4MXJyNo+TV8Hs4//EEbPbiDoo+dmNg22f2RJC282aSwgyWv/O6s3h42qrA6iHx8yfw=", "email_addr": "admin@localhost.local", "role": "admin", "creation_date": "'+now+'", "desc": "admin test user"}}')

    if not isfile(userdb_dir+'/roles.json'):
        with open(userdb_dir+'/roles.json', 'w') as f:
            f.write('{"admin": 100}')

    aaa = Cork(userdb_dir)

    return aaa

def setPassword(aaa, username, new_password):
    pass
