#!/usr/bin/env python

import re


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

        db.execute("""
         INSERT INTO rules (priority, rule, action)
         VALUES(?, ?, ?)
        """, (data['priority'], data['rule'], data['action']))

        c = db.execute("""
          SELECT rules.id as id, priority, rule, actions.id as action_id, actions.title as action_title
          FROM rules INNER JOIN actions ON(actions.id = rules.action)
          WHERE rules.id = last_insert_rowid()
        """)
        return dict(c.fetchone())

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

def putAction(db, data):
    """
    Given the QuenB database, create a new Action with the given settings
    """
    with db:
        for needed in ['plugin', 'args', 'title', 'description']:
            if needed not in data or not data[needed]:
                data[needed] = ''

        matches = re.match(r'^(\S+)\.([^.]+)$', data['plugin'])
        if matches:
            module = matches.group(1)
            function = matches.group(2)
        else:
            module = None
            function = data['plugin']

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
