"""
hooks for easily monkeypatching modules

since -- 7-18-12 -- Jay
"""

# std modules
import imp
import importlib
import sys
import os
import inspect
import ast
import collections
import types

# 3rd party modules

# first party modules

def _get_patched_name(module_name):
    '''
    get the patched name of the module
    
    module_name -- string -- the name of the module

    return -- string
    '''
    return '__{}_'.format(__name__) + module_name

class Modules(object):
    """
    can capture current state of modules and restore them to the sys module

    parts of this class is shamefully ripped from the eventlet module
    """
    def __init__(self):
        self._saved = {}
        imp.acquire_lock()

    def remove(self, *module_names):
        '''
        this will remove the moduls from sys.modules, call freeze first if you need
        to keep a pointer to the module that is getting removed, otherwise it is lost
        '''
        for module_name in module_names:
            sys.modules.pop(module_name, None)

    def load(self, module_name):
        '''
        this will load a fresh copy of module_name, that means it will freeze an
        existing module with the same name if it exists
        '''
        patched_name = _get_patched_name(module_name)

        ## Remove the old module from sys.modules and reimport it while
        ## the specified modules are in place
        self.freeze(module_name)

        # remove the module from sys.modules so we can re-import it fresh
        # Remove the old module from sys.modules and reimport it while
        # the monkey patched modules are in place
        self.remove(module_name)

        m_patched = None
        if patched_name in sys.modules:
            m_patched = sys.modules[patched_name]
        else:
            # re-import a copy we can patch
            m_patched = importlib.import_module(module_name)
        
        # update sys.modules pointers
        sys.modules[patched_name] = m_patched
        sys.modules[module_name] = m_patched

        return m_patched

    def freeze(self, *module_names):
        """Saves the named modules to the object."""
        for modname in module_names:
            self._saved[modname] = sys.modules.get(modname, None)

    def thaw(self):
        """
        Restores the modules that the saver knows about into sys.modules.
        """
        try:
            for modname, mod in self._saved.iteritems():
                if mod is not None:
                    sys.modules[modname] = mod
                else:
                    if modname in sys.modules:
                        del sys.modules[modname]
        finally:
            imp.release_lock()

def patched(module_name):
    '''
    return a previously patched module
    '''
    patched_name = _get_patched_name(module_name)
    return sys.modules[patched_name]

def has_patched(module_name):
    '''
    true if monkey has patched this module before

    todo -- module_name could also be a module?

    module_name -- string -- the name of the module

    return -- boolean
    '''
    patched_name = _get_patched_name(module_name)
    return patched_name in sys.modules

def patch_function(func, patched_modules):
    """
    Decorator that returns a version of the function that patches
    some modules for the duration of the function call.  This is
    deeply gross and should only be used for functions that import
    network libraries within their function bodies that there is no
    way of getting around.

    this code is shamelessly ripped from eventlet module
    """
    raise NotImplementedError("todo: make this work")
    def patched(*args, **kw):
        saver = SysModuleSaver()
        for name, mod in patched_modules.iteritems():
            saver.save(name)
            sys.modules[name] = mod
        try:
            return func(*args, **kw)
        finally:
            saver.restore()
    return patched

def patch(module_name, patches={}, **kwargs_patches):
    '''
    import module_name and apply the patches to it

    module_name -- string -- the name of the module to import
    patches -- dict -- the keys are functions, classes, or modules that should be
        patched in the module, the value is the patched value you want to replace the
        key with

    return -- module -- the module, all patched up
    '''
    patches.update(kwargs_patches) # combine both dicts

    # canary
    if not patches: raise ValueError("patches dict is empty")
    
    modules = Modules()
    # we are going to re-patch if the module was already patched
    # if you want a previously patched instance, use patched() method
    if has_patched(module_name): modules.remove(module_name) 
    deferred_patches = []
    patched_modules = {}
    
    for name, patch in patches.iteritems():
        
        if name.find('.') > -1:
            #raise NotImplementedError('still need to fix this part')
            # we need to patch something in another level, eg, we need to patch bar.baz in foo
            parent_module_name, patch_name = name.rsplit('.', 2)
            parent_m = modules.load(parent_module_name)
            setattr(parent_m, patch_name, patch)
            patched_modules[parent_module_name] = parent_m
            
        else:
            deferred_patches.append((name, patch))

    # actually load the module
    m = None
    try:
        m = modules.load(module_name)

        # go through and apply all the patches
        for patch_name, patch in deferred_patches:
            setattr(m, patch_name, patch)

        patched_modules[module_name] = m

    finally:
        modules.thaw()

    # add decorator to all functions
    # TODO: make this work, basically, the idea is that every function in the module
    # will get wrapped with a decorator that will do all the sys module manipulation on
    # the method call to make sure modules that are imported in the function also get
    # correctly patched, but that is for the next version
    #for k in patched_modules:
        #for kv, v in inspect.getmembers(patched_modules[k]):
            #if isinstance(v, types.FunctionType) and (hasattr(v, 'func_name') or hasattr(v, 'im_func')):
                #setattr(patched_modules[k], kv, patch_function(v, patched_modules))
    
    return m
     
