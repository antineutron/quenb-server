#!/usr/bin/env python

# From http://www.daniweb.com/software-development/python/code/238387/
import glob, imp, types
from os.path import join, basename, splitext

# Scans a plugin directory for plugins and loads them, returning a dict name => module.
# NB it is not recursive; importPlugins(foo) will not import foo/bar/baz.py, only foo/bar.py.
def importPlugins(plugindir):
    return dict( _load(path) for path in glob.glob(join(plugindir,'[!_]*.py')) )

def _load(path):
    name, ext = splitext(basename(path))
    return name, imp.load_source(name, path)

# Gets a list of all functions in the structure:
# {
#   module_name: {
#     function_name : function_object,
#   }
# }
def listAllFunctions(plugindir):
    all_modules = {}

    # List of all plugin modules available
    modules = importPlugins(plugindir)

    for module_name in modules:
        module_obj = modules[module_name]
        all_modules[module_name] = dict(
          [(fname, fun) for (fname,fun) in module_obj.__dict__.iteritems() if type(fun) == types.FunctionType]
        )
    return all_modules
