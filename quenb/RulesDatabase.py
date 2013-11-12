#!/usr/bin/env python

import json
import random
import string
import hashlib
import hmac
import argparse
import collections
import sqlite3
import datetime
import os
import os.path
import csv
import sys
import operator
import copy
import time
import traceback



def setup(db):
    """
    Populates the initial rules/actions database.
    """
    db.execute("""CREATE TABLE IF NOT EXISTS actions
               (id INTEGER PRIMARY KEY,
               module TEXT,
               function TEXT,
               args TEXT,
               title TEXT, description TEXT)""")

    db.execute("""CREATE TABLE IF NOT EXISTS rules
               (id INTEGER PRIMARY KEY,
               priority INT NOT NULL, rule TEXT,
               action INTEGER NOT NULL,
               FOREIGN KEY(action) REFERENCES actions(id))""")

    # TODO The default action is hit if there is no configuration
    # on the server, so make it something funny.
    db.execute("""INSERT OR IGNORE INTO actions
               (id, module, function, args, title, description)
               VALUES (
                 0, 'quenb-builtin', 'display_url', 'http://placekitten.com/1680/1050',
                 'Default', 'Default rule if nothing else matches'
               )""")

    # There must always be a rule at the bottom. Well, I say there must
    # be.
    if not list(db.execute("SELECT * FROM rules")):
        db.execute("""INSERT OR IGNORE INTO rules
                      (priority, rule, action)
                      VALUES (0, "true", 0)""")


def getRules(db):
    """
    Given the QuenB database, return a result with rule/action tuples
    """
    with db:
        return [dict(row) for row in db.execute("""
          SELECT rules.id AS id, priority, rule, action, module, function, args, title, description
          FROM rules
          INNER JOIN actions
          ON rules.action = actions.id
          ORDER BY priority ASC
        """)]
            
