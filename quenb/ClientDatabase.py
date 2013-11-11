#!/usr/bin/env python

from datetime import datetime, timedelta

def getClients(db, timeslot_seconds=3600):
    """
    Given the QuenB database, returns a list of the clients we've seen recently
    """
    with db:

        clients = []

        # Now - time slot: find anything seen AFTER that
        slot_start = datetime.now() - timedelta(seconds=timeslot_seconds)

        for row in db.execute("""
          SELECT cid, ip, hostname, last_heard
          FROM clients
          WHERE last_heard > ?
          ORDER BY hostname ASC
        """, (slot_start,)):
            clients.append(dict(row))

    return clients

