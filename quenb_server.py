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
API_VERSION = '0.0.3'


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
    return db

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
    (cid, addr, hostname, mac, version, window_width, window_height) = ClientDatabase.getClientDetails(db, bottle.request, session, bottle.request.query)
    session.save()

    return {
        'client_id'       : cid,
        'addr'            : addr,
        'hostname'        : hostname,
        'query_variables' : dict(bottle.request.query),
    }



# This is called via AJAX from the webclient, it returns client instructions/data
@app.get('/display')
@app.get('/display/')
@app.post('/display')
@app.post('/display/')
def get_display(db):

    # Get the client's details
    session = bottle.request.environ['beaker.session']
    (cid, addr, hostname, mac, version, window_width, window_height) = ClientDatabase.getClientDetails(db, bottle.request, session, bottle.request.query)
    session.save()

    # Get datetime as a list of numbers
    now = datetime.datetime.now()
    dt_list = [now.year, now.month, now.day, now.hour, now.minute,
               now.second, now.microsecond]

    client_info = {
        'cid':           cid,
        'client_id':     cid,
        'version':       version,
        'addr':          addr,
        'hostname':      hostname,
        'location':      bottle.request.query.location,
        'mac':           mac,
        'calls':         bottle.request.query.calls,
        'datetime':      dt_list,
        'unixtime':      time.mktime(now.timetuple()),
        'time_year':     now.year,
        'time_month':    now.month,
        'time_day':      now.day,
        'time_hour':     now.hour,
        'time_minute':   now.minute,
        'time_second':   now.second,
        'window_width':  window_width,
        'window_height': window_height,
    }

    response = {'client_facts': {}}

    #print "Client facts: {}".format(client_info)
    for rule in RulesDatabase.getRules(db):
        
        # For each rule determine if it fires/applies
        # if so, then those actions are applied to the output

        # the rules are done from lowest to highest, so the higher
        # the priority, it'll apply the actions LAST, and thus be
        # the set that is sent.

        # Parse the rule and evaluate
        #print "Checking rule ID: {} Priority: {} (rule test is: [{}])".format(rule['id'], rule['priority'], rule['rule'])
        rule_text = rule['rule']
        try:
            #print "Evaluating {} against client info [{}]...".format(rule_text, client_info)
            result = ruler.evaluateRule(rule_text, client_info)
            #print "Finished evaluating, result was: {}".format(result)
        except ParseException as e:
            error("Error parsing rule {},{}".format(rule_text, client_info))
            traceback.print_exc()
            continue

        # Rule matched: Load the action and apply it
        if result:
            (client_code, client_info) = ClientResponse.runAction(PLUGIN_DIR, rule['module'], rule['function'], rule['args'], bottle.request, client_info)
            response.update(client_code)
            
            # If we have any updated client info to return e.g. client ID, merge that in too
            if 'client_facts' in client_info:
                response['client_facts'].update(client_info['client_facts'])
            #print "Ran rule: {} and got code: {}/info: {}".format(rule_text, client_code, client_info)

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

@app.get('/admin/help', template='help')
@app.get('/admin/help/', template='help')
def get_admin_help():
    """
    Help pages for the admin interface. Explains how the whole thing works and how to do stuff.
    You know what a help page is.
    """
    aaa.require(role='admin', fail_redirect='/')
    return {
        'current_user' : aaa.current_user,
    }

@app.get('/admin/password_reset', template='passchange')
@app.get('/admin/password_reset/', template='passchange')
def get_admin_password_reset(db):
    """
    Password reset form.
    """
    aaa.require(role='admin', fail_redirect='/')
    return {
        'current_user' : aaa.current_user,
    }

@app.post('/admin/password_reset', template='passchange')
@app.post('/admin/password_reset/', template='passchange')
def post_admin_password_reset(db):
    """
    Password reset backend.
    """
    aaa.require(role='admin', fail_redirect='/')
    current_user = aaa.current_user
    current_password = post_get('passcurrent')
    new_password = post_get('passnew')
    confirmation = post_get('passconfirm')
    # FIXME eww.
    current_hash = aaa._store.users[current_user.username]['hash']

    # TODO proper error reporting and form highlighting and all that
    if not current_password or not new_password or not confirmation:
        abort(400, "Didn't get all parameters, fill in the damn form")

    # Verify current password is correct FIXME: this is fudgy
    elif not aaa._verify_password(current_user.username, current_password, current_hash):
        abort(400, "Current password was incorrect")

    elif new_password != confirmation:
        abort(400, "New password and confirmation do not match")
    
    current_user.update(pwd=confirmation)

    return {
        'current_user' : current_user,
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
    data = bottle.request.POST
    if bottle.request.json:
        data = bottle.request.json
    action = RulesDatabase.putAction(db, data)
    return {
      'action' : action,
    }

@app.post('/admin/action/:id')
def post_admin_action(db, id):
    """
    """
    aaa.require(role='admin', fail_redirect='/')
    data = bottle.request.POST
    if bottle.request.json:
        data = bottle.request.json
    action = RulesDatabase.postAction(db, id, data)
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
    data = bottle.request.POST
    if bottle.request.json:
        data = bottle.request.json
    rule = RulesDatabase.putRule(db, data)
    return {
      'rule' : rule,
    }

@app.post('/admin/rule/:id')
def post_admin_rule(db, id):
    """
    """
    aaa.require(role='admin', fail_redirect='/')
    data = bottle.request.POST
    if bottle.request.json:
        data = bottle.request.json
    rule = RulesDatabase.postRule(db, id, data)
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


@app.get('/admin/plugin_functions/')
def get_admin_plugin_functions():
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






### Webclient API functions ###

@app.get('/api/ping')
def get_api_ping():
    return json.dumps("pong")

@app.get('/api/version')
def get_api_version(db):
    auth_check(db)
    return json.dumps(API_VERSION)







if __name__ == '__main__':

    p = argparse.ArgumentParser()
    p.add_argument('-d','--debug',action='store_true')
    p.add_argument('--host',default='localhost')
    p.add_argument('--port',default=25009)

    ns = p.parse_args()
    setup(db_path=DB_PATH)
    bottle.debug(ns.debug)

    bottle.run(app_sessioned, host=ns.host, port=ns.port)
