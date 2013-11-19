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
from cork import Cork, AuthException
from cork.sqlite_backend import SQLiteBackend
from beaker.middleware import SessionMiddleware


from quenb import PluginLoader, ParseRules, ClientResponse, Authentication, ClientDatabase, RulesDatabase
from pyparsing import ParseException
from settings import *


app = bottle.Bottle()
plugin = bottle.ext.sqlite.Plugin(dbfile=DB_PATH)
app.install(plugin)

aaa = Authentication.getAAA(USERDB_DIR)

app_sessioned = SessionMiddleware(app, SESSION_OPTS)

ruler = ParseRules.QuenbRuleParser()


# Not a setting really, but change here on upgrade
API_VERSION = '0.0.2'


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

# About QuenB
@app.get('/about', template='about')
@app.get('/about/', template='about')
def get_about():
    try:
        return{'current_user' : aaa.current_user}
    except AuthException:
        return {'current_user': None}


# This returns the webclient page, which is where the signage displays start.
# The page loads some Javascript to poll the server asking it what to display, etc.
@app.get('/webclient', template='webclient')
@app.get('/webclient/', template='webclient')
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
@app.get('/display/')
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
@app.post('/login/')
def login():
    username = post_get('username')
    password = post_get('password')
    aaa.login(username, password, success_redirect='/admin', fail_redirect='/')

@app.post('/logout')
@app.post('/logout/')
def logout():
    aaa.logout(success_redirect='/', fail_redirect='/admin')





### Admin pages ###
@app.get('/admin', template='admin')
@app.get('/admin/', template='admin')
def get_admin(db):
    """
    Admin page - by default, just lists the currently connected clients.
    """
    aaa.require(role='admin', fail_redirect='/')
    return {
        'current_user' : aaa.current_user,
        'clients' : ClientDatabase.getClients(db),
    }


@app.get('/admin/actions')
@app.get('/admin/actions/')
def get_admin_actions(db):
    """
    Actions admin page - lists the existing actions so the administrator can
    edit/delete them, and provides a link to add a new action.
    """
    aaa.require(role='admin', fail_redirect='/')

    # AJAX-style JSON request: just return the list of actions
    if(bottle.request.content_type == 'application/json'):
        return {
          'actions' : RulesDatabase.getActions(db),
        }
    # Default: do templatey things
    else:
        return bottle.template('actions.tpl', {
          'current_user' : aaa.current_user,
          'actions' : RulesDatabase.getActions(db),
          'plugins' : PluginLoader.listAllFunctions(PLUGIN_DIR),
        })


@app.get('/admin/action/:id')
def get_admin_action(db, id):
    """
    """

    aaa.require(role='admin', fail_redirect='/')
    action = RulesDatabase.getAction(db, id)
    if not action:
        bottle.abort(404, 'unknown action ID '+str(id))

    # AJAX-style JSON request: just return the list of actions
    if(bottle.request.content_type == 'application/json'):
        return {
          'action' : action,
        }

    # Default: do templatey things
    else:
        return bottle.template('action.tpl', {
          'current_user' : aaa.current_user,
          'action' : action,
        })


@app.put('/admin/action')
def put_admin_action(db):
    """
    """
    aaa.require(role='admin', fail_redirect='/')
    action = RulesDatabase.putAction(db, bottle.request.POST)
    return {
      'action' : action,
    }

@app.post('/admin/action/:id')
def post_admin_action(db):
    """
    """
    aaa.require(role='admin', fail_redirect='/')
    action = RulesDatabase.postAction(db, id, bottle.request.POST)
    return {'action' : action}

@app.delete('/admin/action/:id')
def delete_admin_action(db, id):
    """
    """
    aaa.require(role='admin', fail_redirect='/')

    # Don't allow deleting the default action
    if int(id) == 0:
        bottle.abort(403, 'Cannot delete default action')

    action = RulesDatabase.deleteAction(db, id)
    return {}



@app.get('/admin/rules')
@app.get('/admin/rules/')
def get_admin_rules(db):
    """
    Rules admin page - lists the existing rules so the administrator can
    edit/delete them, and provides a link to add a new rule.
    """
    aaa.require(role='admin', fail_redirect='/')

    # AJAX-style JSON request: just return the list of rules
    if(bottle.request.content_type == 'application/json'):
        return {
          'rules' : RulesDatabase.getRules(db),
        }
    # Default: do templatey things
    else:
        return bottle.template('rules.tpl', {
          'current_user' : aaa.current_user,
          'rules' : RulesDatabase.getRules(db),
          'actions' : RulesDatabase.getActions(db),
        })


@app.get('/admin/rule/:id')
def get_admin_rule(db, id):
    """
    """

    aaa.require(role='admin', fail_redirect='/')
    rule = RulesDatabase.getRule(db, id)
    if not rule:
        bottle.abort(404, 'unknown rule ID '+str(id))

    # AJAX-style JSON request: just return the list of rules
    if(bottle.request.content_type == 'application/json'):
        return {
          'rule' : rule,
        }

    # Default: do templatey things
    else:
        return bottle.template('rule.tpl', {
          'current_user' : aaa.current_user,
          'rule' : rule,
        })


@app.put('/admin/rule')
def put_admin_rule(db):
    """
    """
    aaa.require(role='admin', fail_redirect='/')
    rule = RulesDatabase.putRule(db, bottle.request.POST)
    return {
      'rule' : rule,
    }

@app.post('/admin/rule/:id')
def post_admin_rule(db):
    """
    """
    aaa.require(role='admin', fail_redirect='/')
    rule = RulesDatabase.postRule(db, id, bottle.request.POST)
    return {'rule' : rule}

@app.delete('/admin/rule/:id')
def delete_admin_rule(db, id):
    """
    """
    aaa.require(role='admin', fail_redirect='/')

    # Don't allow deleting the default rule
    if int(id) == 0:
        bottle.abort(403, 'Cannot delete default rule')

    rule = RulesDatabase.deleteRule(db, id)
    return {}







@app.get('/admin/api/plugin_functions/')
def get_admin_api_plugin_functions():
    """
    List all available plugin functions (as modulename.function)
    """
    aaa.require(role='admin', fail_redirect='/')
    
    # List all plugins, then compress to a sorted list of 'module.function_name' strings for display
    functions = PluginLoader.listAllFunctions(PLUGIN_DIR)

    # Hackery :-( Needs to return a dict for the dropdown to work
    # in our actions table.
    expanded = {}
    for mod, funs in functions.iteritems():
        for fun in funs:
            expanded[mod+'.'+fun] = mod+'.'+fun
    return expanded






### Client API functions ###

@app.get('/api/ping')
def get_api_ping():
    return json.dumps("pong")

@app.get('/api/version')
def get_api_version(db):
    auth_check(db)
    return json.dumps(API_VERSION)

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
