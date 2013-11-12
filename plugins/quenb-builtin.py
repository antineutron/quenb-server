#!/usr/bin/env python

"""
Built-in outcome functions supplied with QuenB by default.
"""

def display_url(request, client_info, url):
    """
    The most common outcome, simply display a single webpage.
    """
    return ({"display_url": url}, client_info)

def url_cycle(request, client_info, url_list, timeout):
    """
    Cycle through a list of webpages, whowing each one for a set time.
    """
    return ({"url_cycle": url_list, "cycle_timeout": timeout}, client_info)

def special_show(request, client_info, item):
    """
    Shows a special item client-side (usually a placeholder image).
    """
    return ({"special_show": item}, client_info)

def display_image(request, client_info, image_url):
    """
    Shows an image loaded via a URL (it will be displayed fullscreen like a special_show image).
    """
    return ({"display_image": image_url}, client_info)

def show_logo(request, client_info, args):
    """
    Shows a mandelbrot pattern logo thing.
    """
    return display_image(request, client_info, '/static/mandelbrot.jpg')

def show_error(request, client_info, message):
    """
    Displays an error notification at the top of the screen.
    """
    return({"error": message}, client_info)

def show_info(request, client_info, message):
    """
    Displays an informational notification at the top of the screen.
    """
    return({"info": message}, client_info)

def show_clientid(request, client_info, args):
    """
    Displays a notification of the client ID at the top of the screen.
    """
    if 'cid' in client_info:
        cid = client_info['cid']
    else:
        mac = '(unknown)'
    return({"info": "Client ID: {}".format(cid)}, client_info)

def show_mac(request, client_info, args):
    """
    Displays a notification of the reported MAC address at the top of the screen.
    """
    if 'mac' in client_info:
        mac = client_info['mac']
    else:
        mac = '(unknown)'
    return({"info": "MAC address: {}".format(mac)}, client_info)
