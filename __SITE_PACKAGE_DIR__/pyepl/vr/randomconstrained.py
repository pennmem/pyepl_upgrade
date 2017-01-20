# PyEPL: vr/randomconstrained.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
"""

import random

def demutify(m):
    """
    """
    if isinstance(m, Mutable):
        return m.get()
    return m

def mutapply(func, *targs, **dargs):
    """
    """
    return Mutable(lambda *targs, **dargs: func(*map(demutify, targs), **dict(zip(dargs.iterkeys(), map(demutify, dargs.itervalues())))), *targs, **dargs)

class MutableMethod:
    """
    """
    def __init__(self, obj, attr):
        """
        """
        self.obj = obj
        self.attr = attr
    def __call__(self, *targs, **dargs):
        """
        """
        return Mutable(lambda meth, *targs, **dargs: getattr(meth.obj.get(), meth.attr)(*map(demutify, targs),
                                                                                        **dict(zip(dargs.iterkeys(), map(demutify, dargs.itervalues())))),
                       self, *targs, **dargs)

class Mutable:
    """
    """
    def __init__(self, *targs, **dargs):
        """
        """
        if len(targs) or len(dargs):
            self.set(*targs, **dargs)
        else:
            self.set(NotImplemented)
    def __repr__(self):
        """
        """
        return "<Mutable: %s>" % repr(self.get())
    def __str__(self):
        """
        """
        return str(self.get())
    def __getattr__(self, name):
        """
        """
        if name == "__coerce__" or name == "__hash__":
            raise AttributeError
        o = self.get()
        a = getattr(o, name)
        if callable(a):
            return MutableMethod(self, name)
        else:
            return Mutable(lambda obj, name: getattr(obj, name), o, name)
    def __lt__(self, other):
        """
        """
        return Mutable(lambda a, b: a.get() < demutify(b), self, other)
    def __le__(self, other):
        """
        """
        return Mutable(lambda a, b: a.get() <= demutify(b), self, other)
    def __eq__(self, other):
        """
        """
        return Mutable(lambda a, b: a.get() == demutify(b), self, other)
    def __ne__(self, other):
        """
        """
        return Mutable(lambda a, b: a.get() != demutify(b), self, other)
    def __gt__(self, other):
        """
        """
        return Mutable(lambda a, b: a.get() > demutify(b), self, other)
    def __ge__(self, other):
        """
        """
        return Mutable(lambda a, b: a.get() >= demutify(b), self, other)
    def __len__(self):
        """
        """
        return len(self.get())
    def __iter__(self):
        """
        """
        return iter(self.get())
    def __nonzero__(self):
        """
        """
        return bool(self.get())
    def contains(self, other):
        """
        """
        return Mutable(lambda a, b: demutify(b) in a.get(), self, other)
    def length(self):
        """
        """
        return Mutable(lambda x: len(x.get()), self)
    def get(self):
        """
        """
        return self.func(*self.targs, **self.dargs)
    def set(self, func, *targs, **dargs):
        """
        """
        if callable(func):
            self.func = func
            self.targs = targs
            self.dargs = dargs
        elif isinstance(func, Mutable):
            self.func = func.func
            self.targs = func.targs
            self.dargs = func.dargs
        else:
            self.func = lambda x: x
            self.targs = (func,)
            self.dargs = {}

class AssertionBlockItem:
    """
    """
    def operate(self):
        """
        """
        pass

class RandomFloatItem(AssertionBlockItem):
    """
    """
    def __init__(self, target, min, max):
        """
        """
        self.target = target
        self.min = min
        self.max = max
    def operate(self):
        """
        """
        self.target.set(random.uniform(demutify(self.min), demutify(self.max)))
        return True

class RandomIntItem(AssertionBlockItem):
    """
    """
    def __init__(self, target, min, max):
        """
        """
        self.target = target
        self.min = min
        self.max = max
    def operate(self):
        """
        """
        self.target.set(random.randint(demutify(self.min), demutify(self.max)))
        return True

class RandomChoiceItem(AssertionBlockItem):
    """
    """
    def __init__(self, target, seq):
        """
        """
        self.target = target
        self.seq = seq
    def operate(self):
        """
        """
        self.target.set(random.choice(demutify(self.seq)))
        return True

class RandomSampleItem(AssertionBlockItem):
    """
    """
    def __init__(self, target, population, k):
        """
        """
        self.target = target
        self.population = population
        self.k = k
    def operate(self):
        """
        """
        self.target.set(random.sample(demutify(self.population), demutify(self.k)))
        return True

class AssertionItem(AssertionBlockItem):
    """
    """
    def __init__(self, condition):
        """
        """
        self.condition = condition
    def operate(self):
        """
        """
        return bool(demutify(self.condition))

class AssertionBlock(AssertionBlockItem):
    """
    """
    def __init__(self):
        """
        """
        self.items = []
    def operate(self):
        """
        """
        self.randomize()
        return True
    def randomize(self):
        """
        """
        go = True
        while go:
            go = False
            for item in self.items:
                if not item.operate():
                    go = True
                    break
    def randomFloat(self, min = 0.0, max = 1.0):
        """
        """
        r = Mutable()
        self.items.append(RandomFloatItem(r, min, max))
        return r
    def randomInt(self, min, max):
        """
        """
        r = Mutable()
        self.items.append(RandomIntItem(r, min, max))
        return r
    def randomChoice(self, seq):
        """
        """
        r = Mutable()
        self.items.append(RandomChoiceItem(r, seq))
        return r
    def randomSample(self, population, k = None):
        """
        """
        if k == None:
            k = len(population)
        r = Mutable()
        self.items.append(RandomSampleItem(r, population, k))
        return r
    def assertion(self, condition):
        """
        """
        self.items.append(AssertionItem(condition))
    def subBlock(self):
        """
        """
        r = AssertionBlock()
        self.items.append(r)
        return r
