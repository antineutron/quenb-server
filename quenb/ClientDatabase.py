#!/usr/bin/env python

from datetime import datetime, timedelta

def setup(db):
    """
    Creates the clients database
    """
    db.execute("""CREATE TABLE IF NOT EXISTS clients
               (cid TEXT PRIMARY KEY,
               ip TEXT,
               hostname TEXT,
               last_heard TIMESTAMP)""")


def getClients(db, timeslot_seconds=3600):
    """
    Given the QuenB database, returns a list of the clients we've seen recently
    """
    with db:

        # Now - time slot: find anything seen AFTER that
        slot_start = datetime.now() - timedelta(seconds=timeslot_seconds)

        return [dict(row) for row in db.execute("""
          SELECT cid, ip, hostname, last_heard
          FROM clients
          WHERE last_heard > ?
          ORDER BY hostname ASC
        """, (slot_start,))]


