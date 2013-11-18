#!/usr/bin/python2.7
# Not sure if this will ever be run, but the hashbang acts as a hint
# to vim for python syntax highlighting
import os
import os.path
import sys

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, '.')

import quenb_server, settings

print "Setup: {}".format(settings.DB_PATH)

application = quenb_server.app_sessioned
quenb_server.setup(settings.DB_PATH)
