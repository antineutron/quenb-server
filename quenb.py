#!/usr/bin/python

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

from util import get_hash, generate_token
import scheme

def error(M):
    sys.stderr.write(str(M))
    sys.stderr.write("\n")

def evaluate(expression, environment=None):
    # Given a rule, and a set of information, does the rule fire or not.
    # A rule is a scheme expression, which either returns a truthy value
    # or a false value.
    result, env = scheme.evaluate_string(expression, environment)
    return result

def get_location(geodb, addr):
    # TODO Currently the geoip stuff only supports IPv4, which should
    # change. Although, let's be honest, the IPv6 GeoIP databases are
    # tiny, mostly because of tiny IPv6 deployment. :(

    # Simple v4 detection
    if '.' in addr:
        # Convert v4 address to number
        numbers = [int(i) for i in addr.split('.')]
        integer_ip = 2**24 * numbers[0]
        integer_ip += 2**16 * numbers[1]
        integer_ip += 2**8 * numbers[2]
        integer_ip += numbers[3]

        with geodb:
            cur = geodb.execute("""SELECT * FROM blocks, location WHERE
                                ? BETWEEN blocks.start_ip AND blocks.end_ip
                                AND blocks.loc_id = location.id""",
                                (integer_ip,))
            rows = list(cur)
            if rows:
                row = rows.pop()

                city = row['city']
                region = row['region']
                country = row['country']

                lat = row['latitude']
                lon = row['longitude']

                name = "{}, {}, {}".format(city, region, country)
                loc = "{},{}".format(lat, lon)
                return loc, name

    return None, None

STATIC_FILES = './static'
app = bottle.Bottle()

@app.get('/display')
def get_display(db, geodb=None):
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

    if geodb is not None:
        if query.loc:
            loc = tuple([query.loc.split(',')])
            locname = None
        else:
            # Now based on that IP address
            # look up their geographical location
            loc, locname = get_location(geodb, addr)

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
        'loc': loc,
        'locname': locname,
        'mac': query.mac,
        'calls': query.calls,
        'token': query.token,
        'datetime': dt_list,
        'unixtime': time.mktime(now.timetuple())

    }

    scheme_bodies = []
    with db:
        for code_tuple in db.execute("SELECT * FROM code"):
            scheme_bodies.append(code_tuple['body'])

    template_env = scheme.get_default_environment()

    for item in client_info.items():
        template_env.add_item(item)

    for body in scheme_bodies:
        try:
            value = evaluate(body, template_env)
        except scheme.SchemeException as e:
            error("Error with code {},{}".format(body, e))
            traceback.print_exc()

    # the client_info is passed to the rules engine to determine
    # if a rule's outcome will fire.

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

            rule = ruletuple['rule']
            if rule is not None:
                # Copy a new environment
                env = copy.deepcopy(template_env)
                try:
                    value = evaluate(rule, env)
                except (scheme.SchemeException, Exception) as e:
                    error("Error with rule {},{}".format(rule, client_info))
                    value = False
                    traceback.print_exc()

            if rule is not None and value:
                # get outcome, evaluate it, and apply it to the response
                outcome_id = ruletuple['outcome']

                outcomes = db.execute("SELECT * FROM outcomes WHERE id=?",
                                      (outcome_id,))
                outcomes = list(outcomes)

                if outcomes:
                    outcometuple = outcomes.pop()

                    code = outcometuple['code']
                    # Another new environment
                    env = copy.deepcopy(template_env)
                    try:
                        result = evaluate(code, env)
                        # The return value needs to be a list of (key,value)
                        # pairs
                        settings = dict(result)

                    except (scheme.SchemeException, Exception) as e:
                        error("Error with outcome {},{},{}".format(code,
                                                                client_info,
                                                                  e))
                        settings = {}
                        traceback.print_exc()

                    response.update(settings)

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

@app.get('/api/code')
def get_api_code(db):
    auth_check(db)
    L = database_dump(db, "code")
    return json.dumps(L)

@app.put('/api/code')
@app.put('/api/code/<id>')
def put_api_code(db, id=None):
    auth_check(db)
    database_update(db, "code", id, dict(bottle.request.forms),
                    ['body','title', 'id'])
    return json.dumps(None)

@app.delete('/api/code/<id>')
def delete_api_code(db, id=None):
    auth_check(db)
    with db:
        db.execute("DELETE FROM code WHERE id=?", (id,))
    return json.dumps(None)

def setup(db_path="quenb.db", geodb_path=None):
    db = sqlite3.connect(db_path)
    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS clients
                   (cid TEXT PRIMARY KEY,
                   last_heard TIMESTAMP)""")
        db.execute("""CREATE TABLE IF NOT EXISTS outcomes
                   (id INTEGER PRIMARY KEY,
                   code TEXT,
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
        db.execute("""CREATE TABLE IF NOT EXISTS code
                   (id INTEGER PRIMARY KEY ASC,
                   title TEXT,
                   body TEXT)""")

        # TODO The default outcome is hit if there is no configuration
        # on the server, so make it something funny.
        db.execute("""INSERT OR IGNORE INTO outcomes
                   (id, code)
                   VALUES (0,
                          '(quote (("display_url" "http://nyan.cat")))'
                          )""")

        # There must always be a rule at the bottom. Well, I say there must
        # be.
        if not list(db.execute("SELECT * FROM rules")):
            db.execute("""INSERT OR IGNORE INTO rules
                          (priority, rule, outcome)
                          VALUES (0, "#t", 0)""")

        if not list(db.execute("SELECT * FROM code")):
            db.execute("""INSERT OR IGNORE INTO code
                       (id, title, body)
                       VALUES (0, "Example Code", '(define foo "bar")')""")

        if not list(db.execute("SELECT * FROM users")):
            db.execute("""INSERT OR IGNORE INTO users
                       (username, salt, hash, hash_version)
                       VALUES ("root", "", "root", 0)""")

    plugin = bottle.ext.sqlite.Plugin(dbfile=db_path)
    global app
    app.install(plugin)

    # The geodatabase takes a significant amount of time to create
    # so we're not just doing every time the server starts. That's silly.
    if geodb_path is not None:
        plugin2 = bottle.ext.sqlite.Plugin(dbfile=geodb_path,keyword='geodb')
        # Monkey patch plugins to have different names, so they both work
        plugin2.name += "2"
        app.install(plugin2)

def create_geodb(geodb_path="geoip.db", geoip_folder='.'):
    db = sqlite3.connect(geodb_path)
    db.text_factory = str
    with db:
        db.execute("""CREATE TABLE blocks
                   (start_ip INTEGER, end_ip INTEGER, loc_id INTEGER)""")
        db.execute("""CREATE TABLE location
                   (id INTEGER PRIMARY KEY, country TEXT, region TEXT,
                   city TEXT, postcode TEXT, latitude TEXT, longitude TEXT,
                   metrocode INTEGER, areacode INTEGER)""")

        print("Importing Blocks")
        path = os.path.join(geoip_folder, "GeoLiteCity-Blocks.csv")
        with open(path) as f:
            # Chop the first two lines off
            f.readline()
            f.readline()
            for row in csv.reader(f):
                db.execute("INSERT INTO blocks VALUES (?,?,?)", row)

        print("Importing Location")
        path = os.path.join(geoip_folder, "GeoLiteCity-Location.csv")
        with open(path) as f:
            f.readline()
            f.readline()
            for row in csv.reader(f):
                db.execute("INSERT INTO location VALUES (?,?,?,?,?,?,?,?,?)",
                           row)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-d','--debug',action='store_true')
    p.add_argument('--host',default='localhost')
    p.add_argument('--make-geodb',default='')

    ns = p.parse_args()
    if ns.make_geodb:
        create_geodb(geoip_folder=ns.make_geodb)
    else:
        setup(db_path="quenb.db", geodb_path="geoip.db")
        bottle.debug(ns.debug)

        bottle.run(app, host=ns.host, port=25009)
