#!/usr/bin/env python
"""
Built-in outcome functions supplied with QuenB by default. Should do enough for most standard displays.
"""

from random import randint


def display_url(args, request, client_info):
    """
    The most common outcome, simply display a single webpage.
    """
    return ({"display_url": args[0]}, client_info)

def url_cycle(url_list, request, client_info):
    """
    Cycle through a list of webpages, showing each one in order for a set time.
    """

    # How many requests has the client made? Use this to
    # determine the position in the cycle. Note the -1
    # so that the first request will pick the 0th element.
    if 'calls' in client_info:
        try:
            calls = int(client_info['calls']) - 1
        except:
            calls = 0
    else:
        calls = 0

    next_url = url_list[ calls % len(url_list) ]

    return display_url([next_url], request, client_info)

def url_cycle_random(url_list, request, client_info):
    """
    Cycle through a list of webpages, showing each one at random for a set time.
    """

    next_url = url_list[ randint(0, len(url_list)-1) ]

    return display_url([next_url], request, client_info)

def special_show(args, request, client_info):
    """
    Shows a special item client-side (usually a placeholder image).
    """
    item = args[0]
    return ({"special_show": item}, client_info)

def display_image(args, request, client_info):
    """
    Shows an image loaded via a URL (it will be displayed fullscreen like a special_show image).
    """
    image_url = args[0]
    return ({"display_image": image_url}, client_info)

def show_logo(args, request, client_info):
    """
    Shows a mandelbrot pattern logo thing.
    """
    return display_image('/static/mandelbrot.jpg', request, client_info)

def show_error(args, request, client_info):
    """
    Displays an error notification at the top of the screen.
    """
    message = args[0]
    return({"error": message}, client_info)

def show_info(args, request, client_info):
    """
    Displays an informational notification at the top of the screen.
    """
    message = args[0]
    return({"info": message}, client_info)

def show_clientid(args, request, client_info):
    """
    Displays a notification of the client ID at the top of the screen.
    """
    if 'cid' in client_info:
        cid = client_info['cid']
    else:
        cid = '(unknown)'
    return({"info": "Client ID: {}".format(cid)}, client_info)

def show_mac(args, request, client_info):
    """
    Displays a notification of the reported MAC address at the top of the screen.
    """
    if 'mac' in client_info:
        mac = client_info['mac']
    else:
        mac = '(unknown)'
    return({"info": "MAC address: {}".format(mac)}, client_info)

def set_clientvar(args, request, client_info):
    """
    Sets a specific client info key/value pair, e.g. set cid to "display-1"
    """
    if len(args) > 1:
        client_info[args[0]] = args[1]
        client_info['client_facts'] = {args[0] : args[1]}

    return({}, client_info)

def set_clientid(args, request, client_info):
    """
    Sets the client ID to a new value
    """
    return set_clientvar(['cid', args[0]], request, client_info)

def set_clientgroup(args, request, client_info):
    """
    Assign the client to a specific group
    """
    return set_clientvar(['group', args[0]], request, client_info)

