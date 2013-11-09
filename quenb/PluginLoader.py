#!/usr/bin/env python

# From http://www.daniweb.com/software-development/python/code/238387/
import glob, imp
from os.path import join, basename, splitext

# Scans a plugin directory for plugins and loads them, returning a dict name => module.
# NB it is not recursive; importPlugins(foo) will not import foo/bar/baz.py, only foo/bar.py.
def importPlugins(plugindir):
    return dict( _load(path) for path in glob.glob(join(plugindir,'[!_]*.py')) )

def _load(path):
    name, ext = splitext(basename(path))
    return name, imp.load_source(name, path)


import types
plugins = importPlugins('plugins')
for module in plugins:
    obj = plugins[module]
    functions = [a for a in obj.__dict__.keys() if type(obj.__dict__[a]) == types.FunctionType]
    print "Module: {} Object: {} Functions: {}".format(module, obj, functions)
