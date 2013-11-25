#!/usr/bin/env python

from PluginLoader import *
import types, ipaddress, re, csv
from string import Template

# Which pieces of client info are allowed in parameter substitutions?
# These will be sanitised and substituted, anything else will NOT be
# substituted for security reasons
allowed_client_info = {
  'addr' : 'Client IP address (v4 or v6 allowed)',
  'mac' : 'Client\'s reported MAC address',
  'hostname': 'Client hostname (from reverse DNS entry)',
  'window_width' : 'Client\'s reported window width in pixels',
  'window_height' : 'Client\'s reported window height in pixels',
  'calls' : 'Number of times the client has queried the server',
}


def runAction(plugin_dir, module_name, function_name, function_args, request, client_info):
    """
    Once we've matched a rule for a client and loaded its action,
    load the corresponding plugin (if possible) and run the action
    function. We will pass it the arguments defined in the action
    and also the dict of info we have about the client.
    """

    

    # We will load plugins every time this function is called. It is maybe a little
    # inefficient but it means we don't have to restart when new plugins are added.
    plugins = importPlugins(plugin_dir)

    # Find the corresponding module object
    if module_name not in plugins:
        print "Module {} is not in the plugin list".format(module_name)
        return False

    module_obj = plugins[module_name]

    # And the function, if it's present (and is a function)
    if function_name not in module_obj.__dict__:
        print "Function {} not in module function list".format(function_name)
        return False

    function = module_obj.__dict__[function_name]

    if type(function) != types.FunctionType:
        print "Function {} exists but is not a function! ({})".format(function_name, type(function))
        return False
    
    # Parse the args into a list, possibly with param substitution happening
    function_args = _parseArgs(function_args, client_info)

    response = function(function_args, request=request, client_info=client_info)

    return response
 
def _sanitise(name, value):
    """
    Sanitises client information, if it is a known "fact".
    If we do not know how to sanitise it, return None for that "fact".
    """

    # Lowercase and strip whitespace (most facts will probably need this)
    name = name.strip().lower()
    if isinstance(value, basestring):
        lcstripped = value.strip().lower()

    # IPv4 and IPv6 addresses - attempt to parse and check they are valid
    if name == 'addr':

        try:
            valid_address = ipaddress.ip_address(unicode(lcstripped))
        except ValueError:
            return (name, None)

        # Worked OK, return the stripped value
        return (name, lcstripped)
        
    # MAC addresses - remove colons and dots, check they're a 48-bit hex sequence
    elif name == 'mac':
        mac = re.sub(r'[:.\s]', '', lcstripped)
        if not re.match(r'[a-f0-9]{12}', mac):
            return (name, None)
        return (name, mac)

    # Hostnames: magic

    # Calls, window width and window height must be an integer (can't have 0.3 pixels for example)
    elif name in ['calls', 'window_width', 'window_height']:
        try:
            int(value)
            return (name, value)
        except:
            return (name, None)

    # Default, it's not a thing we will validate
    else:
        return (name, None)

def _parseArgs(function_args, client_info):
    """
    Splits up function arguments using the csv module, then processes
    them against the 'validated' parts of the client info so we can e.g.
    display sites scaled to the right aspect ratio etc.
    """

    # Split args using the csv module
    arg_list = []
    try:
        reader = csv.reader([function_args])
        _arg_list = reader.next()
    except:
        _arg_list = [function_args]

    # Sanitise all the info first
    sanitised_info = {}
    for info in client_info:
        (name, value) = _sanitise(info, client_info[info])
        if value:
            sanitised_info[name] = value
 
    # Now run the given args through SimpleTemplate to do variable replacements
    for arg in _arg_list:
        foo = Template(arg).safe_substitute(sanitised_info)
        arg_list.append(foo)


    return arg_list


if __name__ == '__main__':
    args = 'http://www.youtube.com/user/ecsnews, https://devecs.ecs.soton.ac.uk/, https://society.ecs.soton.ac.uk/events, http://www.ieee.ecs.soton.ac.uk/events.php, http://ecswomen.ecs.soton.ac.uk/links/events, https://www.studentrobotics.org/news/, http://openweathermap.org/, http://www.events.soton.ac.uk/, http://users.ecs.soton.ac.uk/bk8g11/league'

    parsed = _parseArgs(args, {})

    from pprint import pprint
    pprint(parsed)
