import hmac
import hashlib
import random
import string
import subprocess
import re
import logging
import urllib2
import urllib
import base64
import json

logger = logging.getLogger(__name__)

def get_hash(key, path, token, digestmod=hashlib.sha1):
    assert path.startswith('/')
    return hmac.new(key, path + token, digestmod=digestmod).hexdigest()

def generate_token(ran):
    TOKEN_SIZE = 25
    s_list = []
    while len(s_list) < TOKEN_SIZE:
        s_list.append(ran.choice(string.hexdigits))
    return "".join(s_list)

def determine_mac():
    p = subprocess.Popen(('ifconfig',),stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()

    code = p.returncode

    if code != 0:
        # ifconfig went wrong.
        logger.warning("Call to ifconfig failed: {0}".format(code))
        return ()

    pattern = (r'^(\w+)\s+.*HWaddr '
               r'(([abcdef0123456789]{2}:){5}[abcdef0123456789]{2})')

    interfaces = []
    for line in stdout.split('\n'):
        match = re.match(pattern, line)
        if match is not None:
            name = match.group(1)
            addr = match.group(2)

            interfaces.append((name, addr))

    return interfaces

def get_auth_header(username, password):
    base64string = base64.encodestring(
        "{}:{}".format(username, password))[:-1]

    auth_header = "Basic {}".format(base64string)
    return auth_header

def make_requester(host, username, password):
    auth_header = get_auth_header(username, password)
    def requester(path, type='GET', query_dict=None):

        data = None if query_dict is None else urllib.urlencode(query_dict)

        req = urllib2.Request(host + path, data=data)
        req.get_method = lambda: type
        req.add_header("Authorization", auth_header)
        return json.loads(urllib2.urlopen(req).read())
    return requester


