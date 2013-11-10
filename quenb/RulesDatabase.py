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


def getRules(db):
    """
    Given the QuenB database, return a result with rule/outcome tuples
    """
    with db:
        return db.execute("""
          SELECT rule, outcome, module, function, args
          FROM rules
          INNER JOIN outcomes
          ON rules.outcome = outcomes.id
          ORDER BY priority ASC
        """)



def database_dump(db, tablename):
    # Not safe with user input
    L = []
    with db:
        for tuple in db.execute("SELECT * FROM {}".format(tablename)):
            D = dict(zip(tuple.keys(), tuple))
            L.append(D)
    return L

def database_update(db, tablename, id, item, acceptable_keys):
    # db - database connection
    # tablename - the name of the table
    # id - the item to be updated
    # item - the dict of key->value pairs for the update
    # acceptable_keys - a list of keys that are permitted to prevent injection
    with db:
        for key in item.keys():
            if key not in acceptable_keys:
                bottle.abort(400, "Not an acceptable key.")

        if id is not None:
            # Determine if item in present in table.
            stmt = "SELECT * FROM {} WHERE id=?".format(tablename)
            present = False
            for _ in db.execute(stmt, (id,)):
                present = True
                break
        else:
            present = False

        if not present:
            if 'id' in item.keys():
                del item['id']
            # INSERT
            keys, values = item.keys(), item.values()

            params = ','.join(keys)
            qs = ','.join('?' for i in range(len(values)))

            stmt = "INSERT INTO {table} ({params}) VALUES ({qs})"
            stmt = stmt.format(table=tablename, params=params, qs=qs)
            db.execute(stmt, tuple(values))
        else:
            # UPDATE
            for key, value in item.items():
                stmt = "UPDATE {} SET {}=? WHERE id=?".format(tablename, key)
                db.execute(stmt, (value, id))


def setup(db):
    """
    Given the QuenB database, creates rule/outcome tables and defaults if they do not exist.
    """
    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS outcomes
                   (id INTEGER PRIMARY KEY,
                   module TEXT,
                   function TEXT,
                   args TEXT,
                   title TEXT, description TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS rules
                   (id INTEGER PRIMARY KEY,
                   priority INT NOT NULL, rule TEXT,
                   outcome INTEGER,
                   FOREIGN KEY(outcome) REFERENCES outcomes(id))""")

        # TODO The default outcome is hit if there is no configuration
        # on the server, so make it something funny.
        db.execute("""INSERT OR IGNORE INTO outcomes
                   (id, module, function, args, title, description)
                   VALUES (0, 'quenb-builtin', 'display_url', 'http://nyan.cat', 'Nyan Cat', 'Poptart rainbow cat!')""")

        # There must always be a rule at the bottom. Well, I say there must
        # be.
        if not list(db.execute("SELECT * FROM rules")):
            db.execute("""INSERT OR IGNORE INTO rules
                          (priority, rule, outcome)
                          VALUES (0, "true", 0)""")

