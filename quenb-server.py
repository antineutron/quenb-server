#!/usr/bin/env python

import json
import argparse
import sqlite3
import datetime
import sys
import operator
import time
import traceback

import bottle
import bottle.ext.sqlite
from cork import Cork
from cork.sqlite_backend import SQLiteBackend
from beaker.middleware import SessionMiddleware


from quenb import ParseRules, ClientResponse, Authentication, ClientDatabase, RulesDatabase
from pyparsing import ParseException
from settings import *



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




### Helpers ###

def error(M):
    """
    Just prints an error.
    """
    sys.stderr.write(str(M))
    sys.stderr.write("\n")

def post_get(name, default=''):
    """
    Gets data from POST and cleans it up
    """
    return bottle.request.POST.get(name, default).strip()


def setup(db_path="quenb.db"):
    """
    Sets up the initial database tables.
    """
    db = sqlite3.connect(db_path)
    with db:
        RulesDatabase.setup(db)
        ClientDatabase.setup(db)

### Static file handlers ###

@app.get('/favicon.ico')
def get_favicon():
    return bottle.static_file('favicon.ico',root='.')

@app.get('/static/<filename:path>')
def get_static(filename):
    return bottle.static_file(filename, root=STATIC_FILES)


### Browser-rendered pages ###

# Index page, just shows some pretty stuff telling you to log in
@app.get('/', template='index')
def get_index():
    return {}


# This returns the webclient page, which is where the signage displays start.
# The page loads some Javascript to poll the server asking it what to display, etc.
@app.get('/webclient', template='webclient')
def get_webclient(db):

    # Get (or create) the client ID
    session = bottle.request.environ['beaker.session']
    (cid, addr, hostname, mac, version) = ClientDatabase.getClientDetails(db, bottle.request, session, bottle.request.query)
    session.save()

    return {
        'client_id'       : cid,
        'addr'            : bottle.request.remote_addr,
        'query_variables' : dict(bottle.request.query),
    }



# This is called via AJAX from the webclient, it returns client instructions/data
@app.get('/display')
def get_display(db):

    # Get the client's details
    session = bottle.request.environ['beaker.session']
    (cid, addr, hostname, mac, version) = ClientDatabase.getClientDetails(db, bottle.request, session, bottle.request.query)
    session.save()

    # Get datetime as a list of numbers
    now = datetime.datetime.now()
    dt_list = [now.year, now.month, now.day, now.hour, now.minute,
               now.second, now.microsecond]

    client_info = {
        'cid':      cid,
        'version':  version,
        'addr':     addr,
        'location': bottle.request.query.location,
        'mac':      mac,
        'calls':    bottle.request.query.calls,
        'datetime': dt_list,
        'unixtime': time.mktime(now.timetuple())
    }



    response = {}

    for rule in RulesDatabase.getRules(db):
        
        # For each rule determine if it fires/applies
        # if so, then those actions are applied to the output

        # the rules are done from lowest to highest, so the higher
        # the priority, it'll apply the actions LAST, and thus be
        # the set that is sent.

        # Parse the rule and evaluate
        rule_text = rule['rule']
        try:
            result = ruler.evaluateRule(rule_text, client_info)
        except ParseException as e:
            error("Error parsing rule {},{}".format(rule_text, client_info))
            traceback.print_exc()
            continue

        # Rule matched: Load the action and apply it
        if result:
            (client_code, client_info) = ClientResponse.runAction(PLUGIN_DIR, rule['module'], rule['function'], rule['args'], bottle.request, client_info)
            response.update(client_code)

    return json.dumps(response)




### Authentication pages ###
@app.post('/login')
def login():
    username = post_get('username')
    password = post_get('password')
    aaa.login(username, password, success_redirect='/admin', fail_redirect='/')

@app.post('/logout')
def logout():
    aaa.logout(success_redirect='/', fail_redirect='/admin')





### Admin pages ###

@authorize(role="admin")
@app.get('/admin', template='admin')
def get_admin(db):
    """
    Admin page - by default, just lists the currently connected clients.
    """
    return {
        'clients' : ClientDatabase.getClients(db),
    }


@authorize(role="admin")
@app.get('/admin/rules', template='rules')
def get_admin_rules(db):
    """
    Rules admin page - lists the existing rules so the administrator can
    edit/delete them, and provides a link to add a new rule
    """
    return {
      'rules' : RulesDatabase.getRules(db),
    }
    
@authorize(role="admin")
@app.get('/admin/rules/add', template='add_rule')
def get_admin_add_rule(db):
    return {}

@authorize(role="admin")
@app.get('/admin/rules/edit/:rule_id', template='admin_rule')
def get_admin_edit_rule(db, rule_id):
    return {}
    
@authorize(role="admin")
@app.get('/admin/rules/delete:rule_id', template='admin_delete_rule')
def get_admin_delete_rule(db):
    return {}




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

#@app.get('/api/clients')
#def get_api_clients(db):
#    auth_check(db)
#    return json.dumps(database_dump(db, "clients"))

#@app.get('/api/actions')
#def get_api_actions(db):
#    auth_check(db)
#    return json.dumps(database_dump(db, "actions"))

@app.put('/api/actions')
@app.put('/api/actions/<id>')
def put_api_actions(db, id=None):
    auth_check(db)
    database_update(db, 'actions', id, dict(bottle.request.forms),
                    ['code', 'title','description', 'id'])
    return json.dumps(None)

@app.delete('/api/actions/<id>')
def delete_api_actions(db, id=None):
    auth_check(db)
    with db:
        db.execute("DELETE FROM actions WHERE id=?", (id,))
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
                    ['priority','rule','action', 'id'])
    return json.dumps(None)

@app.delete('/api/rules/<id>')
def delete_api_rules(db, id=None):
    auth_check(db)
    with db:
        db.execute("DELETE FROM rules WHERE id=?", (id,))
    return json.dumps(None)



if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-d','--debug',action='store_true')
    p.add_argument('--host',default='localhost')

    ns = p.parse_args()
    setup(db_path=DB_PATH)
    bottle.debug(ns.debug)

    bottle.run(app_sessioned, host=ns.host, port=25009)
