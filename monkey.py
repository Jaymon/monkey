"""
hooks for easily monkeypatching and restoring monkey patched code

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

#_monkey_patched = []

# class ModuleInspect(object):
# 
#     def __init__(self, module):
#         self.patched = None
#         self.unpatched = importlib.import_module(module)
#         
#         self.imports = {}
#         
#     def get_unpatched(self):
#         return self.unpatched
#     
#     def get_patched(self):
#         
#         if self.patched is not None: return self.patched
#     
#         m_path = os.path.realpath(inspect.getsourcefile(self.unpatched))
#         caller_src = open(m_path, 'rU').read()
#         ast_tree = compile(caller_src, m_path, 'exec', ast.PyCF_ONLY_AST)
#         
#         self.imports = self._find_imports_from_tree(ast_tree)
#         pout.v(self.imports)
#     
#     def _find_imports_from_tree(self, ast_tree):
#     
#         imports = set()
#         
#         if hasattr(ast_tree, 'name'):
#             pout.v(ast_tree.name)
#         
#         if hasattr(ast_tree, 'body'):
#             # further down the rabbit hole we go
#             if isinstance(ast_tree.body, collections.Iterable):
#                 for ast_body in ast_tree.body:
#                     imports.update(self._find_imports_from_tree(ast_body))
#                 
#         elif hasattr(ast_tree, 'names'):
#             # base case
#             if hasattr(ast_tree, 'module'):
#                 # we are in a from ... import ... statement
# #                 for ast_name in ast_tree.names:
# #                     imports.add((ast_tree.module, None, ast_name.name, ast_name.asname))
#                 pout.v(ast_tree)
#                 
#             else:
#                 # we are in a import ... statement
#                 for ast_name in ast_tree.names:
#                     imports.add((ast_name.name, ast_name.asname, None, None))
#     
#         return imports
#         

class ModuleFreezer(object):
    """
    can capture current state of modules and restore them to the sys module

    parts of this class is shamefully ripped from the eventlet module
    """
    def __init__(self):
        self._saved = {}
        imp.acquire_lock()

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

def _get_patched_name(module_name):
    '''
    get the patched name of the module
    
    module_name -- string -- the name of the module

    return -- string
    '''
    return '__{}_'.format(__name__) + module_name

def get_patched(module_name):
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

def _load_module(module_name, saver):
    patched_name = _get_patched_name(module_name)
    
    # import the module so we can have an unpatched version to restore
    if module_name not in sys.modules:
        m = importlib.import_module(module_name)
        sys.modules[module_name] = m
    
    if patched_name not in sys.modules:
    
        # save the module
        saver.save(module_name)
        #pout.v(id(m))
        
        # remove the module from sys.modules so we can re-import it fresh
        # Remove the old module from sys.modules and reimport it while
        # the specified modules are in place
        sys.modules.pop(module_name, None)
        
        # re-import a copy we can patch
        m_patched = importlib.import_module(module_name)
        
        # update sys.modules pointers
        sys.modules[patched_name] = m_patched
        sys.modules[module_name] = sys.modules[patched_name]

    return sys.modules[patched_name]

def patch_function(func, patched_modules):
    """Decorator that returns a version of the function that patches
    some modules for the duration of the function call.  This is
    deeply gross and should only be used for functions that import
    network libraries within their function bodies that there is no
    way of getting around."""
    
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


def patch(module_name, patches={}):
    '''
    import module_name and apply the patches to it

    module_name -- string -- the name of the module to import
    patches -- dict -- the keys are functions, classes, or modules that should be
        patched in the module, the value is the patched value you want to replace the
        key with

    return -- module -- the module, all patched up
    '''
    if has_patched(module_name): return get_patched(module_name)
    
    m = None
    mfreezer = ModuleFreezer()
    patched_modules = {}
    deferred_patches = []
    
    for name, patch in patches.iteritems():
        
        if name.find('.') > -1:
            # we need to patch something in another level, eg, we need to patch bar.baz in foo
            parent_module_name, patch_name = name.rsplit('.', 2)
            parent_m = _load_module(parent_module_name, saver)
            setattr(parent_m, patch_name, patch)
            
            patched_modules[parent_module_name] = parent_m
            
        else:
            deferred_patches.append((name, patch))

    ## Remove the old module from sys.modules and reimport it while
    ## the specified modules are in place
    sys.modules.pop(module, None)
    try:
        m = _load_module(module, saver)
        
        for patch_name, patch in deferred_patches:
            setattr(m, patch_name, patch)

        patched_modules[module] = m

    finally:
        saver.restore()  ## Put the original modules back

    # add decorator to all functions
    for k in patched_modules:
        for kv, v in inspect.getmembers(patched_modules[k]):
            if isinstance(v, types.FunctionType) and (hasattr(v, 'func_name') or hasattr(v, 'im_func')):
                setattr(patched_modules[k], kv, patch_function(v, patched_modules))
    
    return m
     
