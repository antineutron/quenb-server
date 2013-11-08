#!/usr/bin/python
from __future__ import print_function

import argparse
import urllib2
import urllib
import sys
import getpass
import base64
import shlex
import json
import code
import readline

from util import get_auth_header


def main():
    p = argparse.ArgumentParser()
    p.add_argument('server')
    p.add_argument('-u','--username',default=None)
    p.add_argument('-p','--password',default=None)

    ns = p.parse_args()
    host = ns.server

    # First check the server is there
    try:
        request(host, "/api/ping")
    except urllib2.URLError as e:
        print("Failure to contact server: {}".format(e),file=sys.stderr)
        return 3

    # Server is present, get user/pass

    if ns.username is None:
        username = raw_input("Username: ")
    else:
        username = ns.username

    if ns.password is None:
        password = getpass.getpass("Password: ")
    else:
        password = ns.password

    auth_header = get_auth_header()

    try:
        request(host, "/api/version", auth_header)
    except urllib2.HTTPError as e:
        print("Invalid authentication.",file=sys.stderr)
        # TODO check it's actually a 401
        return 4

    try:
        entry_loop(host, auth_header)
    except KeyboardInterrupt:
        print()

    return 0

def request(host, url, auth_header=None, data=None):
    request = urllib2.Request("{}{}".format(host, url))

    if auth_header is not None:
        request.add_header("Authorization", auth_header)
    if data is not None:
        request.add_data(data)

    f = urllib2.urlopen(request)
    string = f.read()
    try:
        return json.loads(string)
    except ValueError:
        return None

def entry_loop(host, auth_header):
    clients = request(host, "/api/clients", auth_header)
    no = len(clients)
    print("The server is currently aware of {} client(s).".format(no))

    while True:
        try:
            try:
                text = raw_input("jester> ").strip()
            except EOFError:
                print()
                break

            if not text:
                continue

            tokens = shlex.split(text)

            cmd = tokens[0]
            if cmd == 'exit':
                break
            elif cmd == 'ls':
                clients = request(host, "/api/clients", auth_header)
                for client in clients:
                    print(client)
            elif cmd == "urlset":
                if len(tokens) != 3:
                    print("Usage: urlset <cid> <url>")
                    continue

                cid = tokens[1]
                url = tokens[2]
                fmt = "/api/clients/{}/display_url?new_value={}"
                request(host, fmt.format(cid, url), auth_header, data="")
            elif cmd == "specialset":
                if len(tokens) != 3:
                    print("Usage: specialset <cid> <show>")
                    continue
                cid = tokens[1]
                new_show = tokens[2]
                fmt = "/api/clients/{}/display_url?new_value={}"
                request(host, fmt.format(cid, new_show), auth_header, data="")

            elif cmd == "set":
                if len(tokens) != 4:
                    print("Usage: set <cid> <key> <value>")
                    continue

                cid = tokens[1]
                key = tokens[2]
                value = tokens[3]

                fmt = "/api/clients/{}/{}?new_value={}"

                request(host, fmt.format(cid, key, value), auth_header, '')
            elif cmd == "new":
                if len(tokens) != 2:
                    print("Usage: new <cid>")
                    continue

                cid = tokens[1]
                request(host, "/api/clients/{}".format(cid), auth_header, '')

            elif cmd == "delete":
                if len(tokens) != 2:
                    print("Usage: delete <cid>")
                    continue

                cid = tokens[1]
                url = "{}/api/clients/{}".format(host, cid)
                req = urllib2.Request(url)
                req.get_method = lambda: 'DELETE'
                req.add_header("Authorization", auth_header)

                f = urllib2.urlopen(req)

            elif cmd == 'debug':
                print("Starting Python debugger.")
                import pdb; pdb.set_trace()

            else:
                print("Command not recognised.")
        except urllib2.URLError as e:
            print(e)
            continue


if __name__=='__main__':
    sys.exit(main())
