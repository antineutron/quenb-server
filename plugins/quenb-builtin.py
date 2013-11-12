#!/usr/bin/env python

"""
Built-in outcome functions supplied with QuenB by default.
"""

def display_url(url, request, client_info):
    """
    The most common outcome, simply display a single webpage.
    """
    return ({"display_url": url}, client_info)

def url_cycle(url_list, timeout, request, client_info):
    """
    Cycle through a list of webpages, whowing each one for a set time.
    """
    return ({"url_cycle": url_list, "cycle_timeout": timeout}, client_info)

def special_show(item, request, client_info):
    """
    Shows a special item client-side (usually a placeholder image).
    """
    return ({"special_show": item}, client_info)

def display_image(image_url, request, client_info):
    """
    Shows an image loaded via a URL (it will be displayed fullscreen like a special_show image).
    """
    return ({"display_image": image_url}, client_info)

def show_logo(args, request, client_info):
    """
    Shows a mandelbrot pattern logo thing.
    """
    return display_image('/static/mandelbrot.jpg', request, client_info)

def show_error(message, request, client_info):
    """
    Displays an error notification at the top of the screen.
    """
    return({"error": message}, client_info)

def show_info(message, request, client_info):
    """
    Displays an informational notification at the top of the screen.
    """
    return({"info": message}, client_info)

def show_clientid(args, request, client_info):
    """
    Displays a notification of the client ID at the top of the screen.
    """
    if 'cid' in client_info:
        cid = client_info['cid']
    else:
        mac = '(unknown)'
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
