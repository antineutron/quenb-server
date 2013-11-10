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

try:
    import bottle
    import bottle.ext.sqlite
except ImportError:
    sys.path.insert(0, './lib')
    import bottle
    import bottle.ext.sqlite

from quenb.util import get_hash, generate_token
from quenb import ParseRules, ClientResponse
from pyparsing import ParseException

PLUGIN_DIR = './plugins'
STATIC_FILES = './static'

def error(M):
    sys.stderr.write(str(M))
    sys.stderr.write("\n")


app = bottle.Bottle()

ruler = ParseRules.QuenbRuleParser()

@app.get('/display')
def get_display(db):
    query = bottle.request.query
    token = query.token

    # Determine which client is contacting us, and if we can
    # determine what they have been configured to display

    # If they specify an IP address then use that, if not, then
    # use the one we've detected.
    # This is deliberate, as it allows for debugging.
    addr = query.addr or bottle.request.remote_addr

    # Probably needs some verification it's a legit v4 or v6 address
    if ':' in addr:
        addr = addr.split(':')
    else:
        try:
            addr = [int(x) for x in addr.split('.')]
        except ValueError:
            addr = "<invalid-address>"

    # Hopefully the client supplies a client id ("cid"), and then we
    # can easily look the client up. If not,
    # TODO we'll have to determine who the client is likely to be
    # based on the other information they've supplied.
    cid = query.cid

    # If they didn't include a version string, then version is the empty
    # list, otherwise it should be a [NAME, MAJOR, MINOR, PATCH] list
    version = query.version.split(',')

    # Get datetime as a list of numbers
    now = datetime.datetime.now()
    dt_list = [now.year, now.month, now.day, now.hour, now.minute,
               now.second, now.microsecond]

    client_info = {
        'cid': cid,
        'version': version,
        'addr': addr,
        'location': query.location,
        'mac': query.mac,
        'calls': query.calls,
        'token': query.token,
        'datetime': dt_list,
        'unixtime': time.mktime(now.timetuple())

    }


    if cid:
        with db:
            # Insert a entry into the database
            db.execute("INSERT OR IGNORE INTO clients (cid) VALUES (?)",
                       (cid,))
            # Then update the timestamp from when we last heard them.
            db.execute("UPDATE clients SET last_heard = ? WHERE cid = ?",
                       (datetime.datetime.now(), cid))

    response = {}

    with db:
        for ruletuple in db.execute("""SELECT * FROM rules
                                    ORDER BY priority ASC"""):
            # For each rule determine if it fires/applies
            # if so, then those outcomes are applied to the output

            # the rules are done from lowest to highest, so the higher
            # the priority, it'll apply the outcomes LAST, and thus be
            # the set that is sent.

            # Parse the rule and evaluate
            rule = ruletuple['rule']
            try:
                result = ruler.evaluateRule(rule, client_info)
            except ParseException as e:
                error("Error parsing rule {},{}".format(rule, client_info))
                traceback.print_exc()

            # Rule matched: Load the outcome and apply it
            if result:

                outcome_id = ruletuple['outcome']

                outcomes = db.execute("SELECT module, function, args FROM outcomes WHERE id=?",
                                      (outcome_id,))
                outcomes = list(outcomes)

                if outcomes:
                    outcometuple = outcomes.pop()
                    (module_name, function_name, function_args) = outcometuple
                    (client_code, client_info) = ClientResponse.runOutcome(PLUGIN_DIR, module_name, function_name, function_args, client_info)
                    response.update(client_code)
    return json.dumps(response)

@app.get('/webclient')
def get_webclient():

    d = {
        'client_id': get_salt(n=16),
        'addr': bottle.request.remote_addr,
    }

    query = bottle.request.query

    d['query_variables'] = dict(query)

    return bottle.template('webclient', **d)

@app.get('/favicon.ico')
def get_favicon():
    return bottle.static_file('favicon.ico',root='.')

@app.get('/static/<filename:path>')
def get_static(filename):
    return bottle.static_file(filename, root=STATIC_FILES)

def auth_check(db):
    if bottle.request.auth is None:
        bottle.abort(401, "No credentials supplied.")

    username, password = bottle.request.auth
    for usertuple in db.execute("SELECT * FROM users WHERE username=?",
                                (username,)):
        salt, hash_version = usertuple['salt'], usertuple['hash_version']
        if usertuple['hash'] == hash_password(password, salt, hash_version):
            return True

    bottle.abort(401, "Bad credentials.")

def hash_password(password='',salt='',hash_version=1):
    if hash_version == 0:
        # plaintext
        return password

    elif hash_version == 1:
        hash = hashlib.sha512(password + salt).digest()
        for i in range(1000):
            hash = hashlib.sha512(hash + salt).digest()
        return hash
    else:
        raise Exception("Hash version not recognised.")

def get_salt(n=10):
    # Generate random hexstring
    hexstring = ''
    r = random.SystemRandom()
    for i in range(n):
        hexstring += r.choice('1234567890abcedef')
    return hexstring


@app.get('/api/ping')
def get_api_ping():
    return json.dumps("pong")

@app.get('/api/version')
def get_api_version(db):
    auth_check(db)
    #FIXME should probably be the version of the API rather
    # than a hardcoded string
    return json.dumps("0.0.1")

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

@app.get('/api/clients')
def get_api_clients(db):
    auth_check(db)
    return json.dumps(database_dump(db, "clients"))

@app.get('/api/outcomes')
def get_api_outcomes(db):
    auth_check(db)
    return json.dumps(database_dump(db, "outcomes"))

@app.put('/api/outcomes')
@app.put('/api/outcomes/<id>')
def put_api_outcomes(db, id=None):
    auth_check(db)
    database_update(db, 'outcomes', id, dict(bottle.request.forms),
                    ['code', 'title','description', 'id'])
    return json.dumps(None)

@app.delete('/api/outcomes/<id>')
def delete_api_outcomes(db, id=None):
    auth_check(db)
    with db:
        db.execute("DELETE FROM outcomes WHERE id=?", (id,))
    return json.dumps(None)


@app.get('/api/rules')
def get_api_rules(db):
    auth_check(db)
    L = database_dump(db, "rules")
    L.sort(key=operator.itemgetter('priority'))
    return json.dumps(L)

@app.put('/api/rules')
@app.put('/api/rules/<id>')
def put_api_rules(db, id=None):
    auth_check(db)
    database_update(db, "rules", id, dict(bottle.request.forms),
                    ['priority','rule','outcome', 'id'])
    return json.dumps(None)

@app.delete('/api/rules/<id>')
def delete_api_rules(db, id=None):
    auth_check(db)
    with db:
        db.execute("DELETE FROM rules WHERE id=?", (id,))
    return json.dumps(None)

def setup(db_path="quenb.db"):
    db = sqlite3.connect(db_path)
    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS clients
                   (cid TEXT PRIMARY KEY,
                   last_heard TIMESTAMP)""")
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
        db.execute("""CREATE TABLE IF NOT EXISTS users
                   (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                   salt TEXT NOT NULL,
                   hash TEXT NOT NULL,
                   hash_version INT NOT NULL)""")

        # TODO The default outcome is hit if there is no configuration
        # on the server, so make it something funny.
        db.execute("""INSERT OR IGNORE INTO outcomes
                   (id, module, function, args)
                   VALUES (0, 'quenb-builtin', 'display_url', 'http://nyan.cat')""")

        # There must always be a rule at the bottom. Well, I say there must
        # be.
        if not list(db.execute("SELECT * FROM rules")):
            db.execute("""INSERT OR IGNORE INTO rules
                          (priority, rule, outcome)
                          VALUES (0, "true", 0)""")

#        if not list(db.execute("SELECT * FROM code")):
#            db.execute("""INSERT OR IGNORE INTO code
#                       (id, title, body)
#                       VALUES (0, "Example Code", '(define foo "bar")')""")
#
#        if not list(db.execute("SELECT * FROM users")):
#            db.execute("""INSERT OR IGNORE INTO users
#                       (username, salt, hash, hash_version)
#                       VALUES ("root", "", "root", 0)""")

    plugin = bottle.ext.sqlite.Plugin(dbfile=db_path)
    global app
    app.install(plugin)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-d','--debug',action='store_true')
    p.add_argument('--host',default='localhost')

    ns = p.parse_args()
    setup(db_path="quenb.db")
    bottle.debug(ns.debug)

    bottle.run(app, host=ns.host, port=25009)
