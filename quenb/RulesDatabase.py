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
                 0, 'quenb-builtin', 'display_image', 'http://placekitten.com/1680/1050',
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

def updateRuleField(db, rule_id, field, value):
    """
    Updates a specific field for a rule, used by the fancy-schmancy rules editing table to edit a field at a time.
    """
    with db:
        # A bit hacky, but works around the problem of identifiers not being parameterisable
        field = field.strip().lower()
        if field in ['priority', 'rule', 'action']:
            
            db.execute("""
            UPDATE rules
            SET {} = ?
            WHERE id = ?
            """.format(field), (value, rule_id))

            # Send back whatever's in the database, whether updated or not
            return [row[0] for row in db.execute("""
            SELECT {} FROM rules WHERE id=?
            """.format(field), (rule_id,))][0]
    
def getActions(db):
    """
    Given the QuenB database, return a result with action tuples
    """
    with db:
        return [dict(row) for row in db.execute("""
          SELECT id, module, function, args, title, description
          FROM actions
          ORDER BY title ASC
        """)]
            
def updateActionField(db, action_id, field, value):
    """
    Updates a specific field for an action, used by the fancy-schmancy action editing table to edit a field at a time.
    """
    with db:
        # A bit hacky, but works around the problem of identifiers not being parameterisable
        field = field.strip().lower()
        if field in ['title', 'description']:
            
            db.execute("""
            UPDATE actions
            SET {} = ?
            WHERE id = ?
            """.format(field), (value, action_id))

            # Send back whatever's in the database, whether updated or not
            return [row[0] for row in db.execute("""
            SELECT {} FROM actions WHERE id=?
            """.format(field), (action_id,))][0]
