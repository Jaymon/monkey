# std modules
import time
import os
import inspect
import copy
import unittest

# first party
import monkey

class MonkeyTest(unittest.TestCase):

    def test_patch_no_patches(self):
        with self.assertRaises(ValueError):
            json_patched = monkey.patch('json')

    def test_patch(self):

        # this one should remain untouched
        import json as json_orig
        import json as json_orig_too
        self.assertEquals(id(json_orig), id(json_orig_too))

        # now let's import a patched one
        def dumps_new(*args, **kwargs):
            return "happy"

        json_patched = monkey.patch('json', dumps=dumps_new)
        self.assertNotEquals(id(json_orig), id(json_patched))

        self.assertEquals("happy", json_patched.dumps({}))

        import json as json_orig_also
        self.assertEquals(id(json_orig), id(json_orig_also))

    def test_patch_one_level(self):
        '''
        makes sure this works for patching module2.func in module, ie, module.module2.func
        will be the monkey patched function
        '''

        # now let's import a patched one
        def patched(*args, **kwargs):
            return "happy"

        copy_patched = monkey.patch('copy', {'weakref.proxy': patched})

        self.assertEquals("happy", copy_patched.weakref.proxy(''))

        import copy as copy_orig
        self.assertNotEquals(id(copy_orig), id(copy_patched))

    
    def test_patch_func_func(self):
        return
        
        def old_func(foo, bar):
            return foo + bar
        
        def new_func(foo, bar):
            return 5 + (foo + bar)
        
        def new_func_2(foo, bar):
            return 10 + (foo + bar) 
        
        self.assertEquals(3, old_func(1, 2))
        old_func = monkey.patch('old_func', new_func)
        self.assertEquals(8, old_func(1, 2))
        
        #old_func = monkey.patch(old_func, new_func_2)
        #self.assertEquals(13, old_func(1, 2))
    
if __name__ == '__main__':
    unittest.main()
