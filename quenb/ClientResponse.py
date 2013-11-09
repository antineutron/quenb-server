#!/usr/bin/env python

from PluginLoader import *
import types



def runOutcome(plugin_dir, module_name, function_name, function_args, client_info):
    """
    Once we've matched a rule for a client and loaded its outcome,
    load the corresponding plugin (if possible) and run the outcome
    function. We will pass it the arguments defined in the outcome
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
    
    print "Run function: {} with args: {} and info: {}".format(function, function_args, client_info)

    response = function(function_args, client_info=client_info)

    return response
    

