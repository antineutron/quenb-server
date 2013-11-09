#!/usr/bin/python
# Not sure if this will ever be run, but the hashbang acts as a hint
# to vim for python syntax highlighting
import os
import os.path
import sys

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, '.')
import quenb-server

application = quenb.app
quenb.setup('/var/lib/quenb/quenb.db')
