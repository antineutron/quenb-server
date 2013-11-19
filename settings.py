#!/usr/bin/env python


# Server-side plugin directory
PLUGIN_DIR = './plugins'

# Where static files are stored
STATIC_FILES = './static'

# Directory for the user "database" (json files for use with Cork)
USERDB_DIR = './userdb'

# Where to store the rules/outcomes database
DB_PATH = 'quenb.db'

# Session options (mostly used for the admin interface)
SESSION_OPTS = {
    'session.cookie_expires': True,
    'session.encrypt_key': 'please use a random key and keep it jksdgjksfgjkbsdfg secret!',
    'session.httponly': True,
    'session.timeout': 3600 * 24,  # 1 day
    'session.type': 'cookie',
    'session.validate_key': True,
}

# Attempt to load secret settings if they exist, to override the defaults
try:
    from secret_settings import *
except:
    pass
