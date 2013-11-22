#!/usr/bin/env python

from datetime import datetime, timedelta
import re, random, socket

def setup(db):
    """
    Creates the clients database
    """
    db.execute("""CREATE TABLE IF NOT EXISTS clients
               (cid TEXT PRIMARY KEY,
               ip TEXT,
               hostname TEXT,
               mac TEXT,
               version TEXT,
               last_heard TIMESTAMP)""")

def getClientDetails(db, request, session, query):
    """
    Returns a tuple of client info: (client ID, IP, hostname, MAC address)

    Gets the client ID, checking for one supplied by the client, then
    one stored in the session, or as a last resort creating one.
    Stores the ID in the session when it's done.
    Gets the client's IP from the request, but may be overridden
    by the client for e.g. debugging purposes.
    The hostname is looked up from the IP, and the MAC address 
    can only be supplied by the client.

    Will auto-update the client DB with 'last seen' info.
    """

    # If the client has supplied a client ID, e.g. for debugging,
    # use that as the first priority
    if 'client_id' in request:
        cid = request.client_id
    elif 'cid' in request:
        cid = request.cid

    # Otherwise, if there is a client ID in the session data,
    # use that...
    elif 'client_id' in session:
        cid = session.get('client_id')

    # Failing all else, generate a random client ID as a 30-digit hex string
    # and store it in the session.
    else:
        cid = '{0:030x}'.format(random.randrange(16**30))

    # Make sure we store the client ID in the session between requests.
    session['client_id'] = cid

    # If they specify an IP address then use that, if not, then
    # use the one we've detected.
    # This is deliberate, as it allows for debugging.
    addr = query.addr or request.remote_addr

    # Attempt to resolve hostname, default to IP
    try:
        hostname = socket.gethostbyaddr(addr)[0]
    except:
        hostname = addr

    # MAC address: remove all but hex chars and lowercase-ify it for matching
    mac = query.mac.lower()
    mac = re.sub(r'[^a-z0-9]', '', mac)

    # If they didn't include a version string, then version is the empty
    # list, otherwise it should be a [NAME, MAJOR, MINOR, PATCH] list
    version = query.version.split(',')

    # Automatically update the client database so we know when they were last seen
    updateClient(db, cid, addr, hostname, mac, version)

    # Window dimensions as reported by the client
    if 'window_width' in query:
        window_width = query.window_width
    else:
        window_width = None
    if 'window_height' in query:
        window_height = query.window_height
    else:
        window_height = None
        

    return (cid, addr, hostname, mac, version, window_width, window_height)

def updateClient(db, cid, addr, hostname, mac, version):
    with db:
        # Insert a entry into the database
        print "cid {} addr {} hostname {} mac {} version {} ".format(cid, addr, hostname, mac, version)
        db.execute("INSERT OR IGNORE INTO clients (cid, ip, hostname, mac, version) VALUES (?, ?, ?, ?, ?)",
                   (cid, addr, hostname, mac, ','.join(version)))
        # Then update the timestamp from when we last heard them.
        db.execute("UPDATE clients SET last_heard = ?, ip = ?, hostname = ?, mac = ?, version = ? WHERE cid = ?",
                   (datetime.now(), addr, hostname, mac, ','.join(version), cid))

def getClients(db, timeslot_seconds=3600):
    """
    Given the QuenB database, returns a list of the clients we've seen recently
    """
    with db:

        # Now - time slot: find anything seen AFTER that
        slot_start = datetime.now() - timedelta(seconds=timeslot_seconds)

        return [dict(row) for row in db.execute("""
          SELECT cid, ip, hostname, mac, version, last_heard
          FROM clients
          WHERE last_heard > ?
          ORDER BY hostname ASC
        """, (slot_start,))]

