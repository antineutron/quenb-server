#!/usr/bin/env python

import json
import random
import string
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
import socket

import bottle
import bottle.ext.sqlite
from cork import Cork
from cork.sqlite_backend import SQLiteBackend
from beaker.middleware import SessionMiddleware


from quenb import ParseRules, ClientResponse, Authentication, ClientDatabase
from pyparsing import ParseException
from settings import *


def error(M):
    sys.stderr.write(str(M))
    sys.stderr.write("\n")


app = bottle.Bottle()
plugin = bottle.ext.sqlite.Plugin(dbfile=DB_PATH)
app.install(plugin)

aaa = Authentication.getAAA(USERDB_DIR)

session_opts = {
    'session.cookie_expires': True,
    'session.encrypt_key': 'please use a random key and keep it jksdgjksfgjkbsdfg secret!',
    'session.httponly': True,
    'session.timeout': 3600 * 24,  # 1 day
    'session.type': 'cookie',
    'session.validate_key': True,
}
app_sessioned = SessionMiddleware(app, session_opts)

authorize = aaa.make_auth_decorator(fail_redirect="/", role="user")

ruler = ParseRules.QuenbRuleParser()

def post_get(name, default=''):
    return bottle.request.POST.get(name, default).strip()

@app.get('/')
@bottle.view('index')
def get_index():
    return {}

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
#    if ':' in addr:
#        addr = addr.split(':')
#    else:
#        try:
#            addr = [int(x) for x in addr.split('.')]
#        except ValueError:
#            addr = "<invalid-address>"

    # Attempt to resolve hostname, default to IP
    try:
        hostname = socket.gethostbyaddr(addr)[0]
    except:
        hostname = addr

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
        'cid':      cid,
        'version':  version,
        'addr':     addr,
        'location': query.location,
        'mac':      query.mac,
        'calls':    query.calls,
        'token':    query.token,
        'datetime': dt_list,
        'unixtime': time.mktime(now.timetuple())

    }


    if cid:
        with db:
            # Insert a entry into the database
            db.execute("INSERT OR IGNORE INTO clients (cid, ip, hostname) VALUES (?, ?, ?)",
                       (cid,addr,hostname))
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
@bottle.view('webclient')
def get_webclient():

    import random
    cid = '{0:030x}'.format(random.randrange(16**30))
    d = {
        #TODO
        'client_id': cid,
        'addr': bottle.request.remote_addr,
    }

    query = bottle.request.query

    d['query_variables'] = dict(query)

    #return bottle.template('webclient', **d)
    return d


@authorize(role="admin")
@app.get('/admin', template='admin')
def get_admin(db):
    return {
        'clients' : ClientDatabase.getClients(db),
    }


@app.post('/login')
def login():
    username = post_get('username')
    password = post_get('password')
    aaa.login(username, password, success_redirect='/admin', fail_redirect='/')

@app.post('/logout')
def logout():
    aaa.logout(success_redirect='/', fail_redirect='/admin')

@app.get('/favicon.ico')
def get_favicon():
    return bottle.static_file('favicon.ico',root='.')

@app.get('/static/<filename:path>')
def get_static(filename):
    return bottle.static_file(filename, root=STATIC_FILES)



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
                   ip TEXT,
                   hostname TEXT,
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


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-d','--debug',action='store_true')
    p.add_argument('--host',default='localhost')

    ns = p.parse_args()
    setup(db_path=DB_PATH)
    bottle.debug(ns.debug)

    bottle.run(app_sessioned, host=ns.host, port=25009)
