#!/usr/bin/env python

import re
from ParseRules import QuenbRuleParser
from bottle import abort

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
                 0, 'quenb-builtin', 'display_image', 'http://placekitten.com/$window_width/$window_height',
                 'Default', 'Default rule if nothing else matches'
               )""")

    # There must always be a rule at the bottom. Well, I say there must
    # be.
    if not list(db.execute("SELECT * FROM rules")):
        db.execute("""INSERT OR IGNORE INTO rules
                      (id, priority, rule, action)
                      VALUES (0, 0, "true", 0)""")


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

def getRule(db, id):
    """
    Given the QuenB database, return a single rule tuple 
    """
    with db:
        return [dict(row) for row in db.execute("""
          SELECT id, module, function, args, title, description
          FROM rules
          WHERE id = ?
        """, id)]

def putRule(db, data):
    """
    Given the QuenB database, create a new Rule with the given settings
    """
    with db:
        for needed in ['priority', 'action', 'rule']:
            if needed not in data or not data[needed]:
                data[needed] = ''

        parser = QuenbRuleParser()
        rule = data['rule']
        if not parser.checkRule(rule):
            abort(400, 'Invalid rule ysntax')

        ok = db.execute("""
         INSERT INTO rules (priority, rule, action)
         VALUES(?, ?, ?)
        """, (data['priority'], data['rule'], data['action']))

        c = db.execute("""
          SELECT rules.id as id, priority, rule, actions.id as action_id, actions.title as action_title
          FROM rules INNER JOIN actions ON(actions.id = rules.action)
          WHERE rules.id = last_insert_rowid()
        """)
        row = c.fetchone()

        if row:
            return dict(row)
        else:
            return None

def postRule(db, id, _data):
    """
    Given the QuenB database, update a Rule with the given settings
    """
    with db:

        # Delete anything we don't like the look of
        data = {}
        for field in _data:
            fieldlc = field.lower().strip()
            if fieldlc in ['priority', 'action', 'rule']:
                data[fieldlc] = _data[field]

        parser = QuenbRuleParser()
        rule = data['rule']
        if not parser.checkRule(rule):
            abort(400, 'Invalid rule ysntax')

        # Build a list of placeholders and values for the SET key=value, key=value clause
        placeholders = []
        fields_values = []
        for field, value in data.iteritems():
            placeholders.append('{} = ?'.format(field))
            fields_values.append(value)
        placeholders = ', '.join(placeholders)

        db.execute("""
         UPDATE rules
         SET {}
         WHERE id = ?
        """.format(placeholders), fields_values + [id])

        c = db.execute("""
          SELECT rules.id as id, priority, rule, actions.id as action_id, actions.title as action_title
          FROM rules INNER JOIN actions ON(actions.id = rules.action)
          WHERE rules.id = ?
        """, (id,))

        row = c.fetchone()

        if row:
            return dict(row)
        else:
            return None

def deleteRule(db, id):
    """
    Given the QuenB database, delete a rule
    """
    with db:
        db.execute("""
          DELETE FROM rules
          WHERE id = ?
        """, (id,))


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

def getAction(db, id):
    """
    Given the QuenB database, return a single action tuple 
    """
    with db:
        return [dict(row) for row in db.execute("""
          SELECT id, module, function, args, title, description
          FROM actions
          WHERE id = ?
        """, id)]

def _plugin2functions(plugin_spec):
    matches = re.match(r'^(\S+)\.([^.]+)$', plugin_spec)
    if matches:
        module = matches.group(1)
        function = matches.group(2)
    else:
        module = None
        function = data['plugin']
 
    return (module, function)

def putAction(db, data):
    """
    Given the QuenB database, create a new Action with the given settings
    """
    with db:
        for needed in ['plugin', 'args', 'title', 'description']:
            if needed not in data or not data[needed]:
                data[needed] = ''

        (module, function) = _plugin2functions(data['plugin'])

        db.execute("""
         INSERT INTO actions (module, function, args, title, description)
         VALUES(?, ?, ?, ?, ?)
        """, (module, function, data['args'], data['title'], data['description']))

        c = db.execute("""
          SELECT id, module, function, args, title, description
          FROM actions
          WHERE id = last_insert_rowid()
        """)
        return dict(c.fetchone())

def postAction(db, id, data):
    """
    Given the QuenB database, update an Action with the given settings
    """
    with db:

        # Delete anything we don't like the look of
        for field in data:
            if field not in ['plugin', 'args', 'title', 'description']:
                del data[field]

        if 'plugin' in data:
            (module, function) = _plugin2functions(data['plugin'])

            del data['plugin']
            data['module'] = module
            data['function'] = function

        # Build a list of placeholders and values for the SET key=value, key=value clause
        placeholders = []
        fields_values = []
        for field, value in data.iteritems():
            placeholders.append('{} = ?'.format(field))
            fields_values.append(value)
        placeholders = ', '.join(placeholders)

        db.execute("""
         UPDATE actions
         SET {}
         WHERE id = ?
        """.format(placeholders), fields_values + [id])

        c = db.execute("""
          SELECT id, module||'.'||function as plugin, args, title, description
          FROM actions
          WHERE id = ?
        """, (id,))

        row = c.fetchone()

        if row:
            return dict(row)
        else:
            return None

def deleteAction(db, id):
    """
    Given the QuenB database, delete an action
    """
    with db:
        db.execute("""
          DELETE FROM actions
          WHERE id = ?
        """, (id,))
            
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
