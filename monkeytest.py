# std modules
import json
import time
import base64
import os
import inspect
import copy

# 3rd party
from django.db import models
from django.test.client import Client as djClient
import eventlet # MultiTest

# first party
from .test.testcases import TestCase
from . import models as djmodels
from . import greenthread
from . import utils
from .fab import django as djfab
from . import profiler
from . import monkey

class MonkeyTest(TestCase):
    
    def test_patch_func_func(self):
        
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
    
    def test_patch_module_func(self):
        
        def new_time():
            return 100
        
        #profiler = monkey.patch('djmod.profiler', funcs={'time.time': new_time})
        tm1 = monkey.patch('djmod.testmod1', patches={'time.time': new_time, 'happy': range(2)})
        pout.v(tm1.click_whirr(), tm1.happy)
        #pout.v(time.time())
        
        import time
        pout.v(time.time())
        
        
        #monkey.unpatch()
        
