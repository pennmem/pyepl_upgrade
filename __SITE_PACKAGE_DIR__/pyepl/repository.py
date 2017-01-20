# PyEPL: repository.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
The repository module.
"""

import weakref

nopickle = []

class WeakRef:
    """
    An extension of the ref class that can be pickled.
    """
    def __init__(self, *targs, **dargs):
        """
        """
        self.r = weakref.ref(*targs, **dargs)
    def __getattr__(self, name):
        """
        """
        return getattr(self.r, name)
    def __getstate__(self):
        """
        """
        return self.r()
    def __setstate__(self, state):
        """
        """
        self.r = weakref.ref(state)

class WeakKeyDictionary(weakref.WeakKeyDictionary):
    """
    An extension of the WeakKeyDictionary class that can be pickled.
    """
    def __getstate__(self):
        """
        Returns a regular dictionary version of the WeakKeyDictionary.
        """
        global nopickle
        d = dict(self)
        for key, value in d.items():
            if type(key) in nopickle:
                del d[key]
        return d
    def __setstate__(self, state):
        """
        Constructs WeakKeyDictionary from state dictionary.
        """
        weakref.WeakKeyDictionary.__init__(self, state)

class WeakValueDictionary(weakref.WeakValueDictionary):
    """
    An extension of the WeakValueDictionary class that can be pickled.
    """
    def __getstate__(self):
        """
        Returns a regular dictionary version of the WeakKeyDictionary.
        """
        global nopickle
        d = dict(self)
        for key, value in d.items():
            if type(value) in nopickle:
                del self[key]
        return dict(self)
    def __setstate__(self, state):
        """
        Constructs WeakKeyDictionary from state dictionary.
        """
        weakref.WeakValueDictionary.__init__(self, state)

class MethodCallback:
    """
    """
    def __init__(self, m):
        """
        """
        self.name = m.im_func.__name__
        self.obj = m.im_self
    def __call__(self, *targs, **dargs):
        """
        """
        getattr(self.obj, self.name)(*targs, **dargs)
