# PyEPL: repospool.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

import pyepl
from repository import ReposDir, ReposRef
import random

def compoundCompare(x, y, *attr):
    """
    """
    for a in attr:
        r = cmp(getattr(x, a), getattr(y, a))
        if r != 0:
            return r
    return 0

class ReposPool:
    """
    """
    def __init__(self, repos = None, size = 0):
        """
        """
        if repos:
            self.repos = repos
        else:
            self.repos = pyepl.repository.mainRepository
        self.pool = [None for x in xrange(size)]
    def append(self):
        """
        """
        r = self.repos.newDir()
        self.pool.append(r)
        return r
    def insert(self, n):
        """
        """
        r = self.repos.newDir()
        self.pool.insert(n, r)
        return r
    def extend(self, p):
        """
        """
        if not isinstance(p, ReposPool):
            raise ValueError, "ReposPool can only be extended with another ReposPool"
        self.pool.extend(p)
    def __getitem__(self, index):
        """
        """
        return self.pool[index]
    def __delitem__(self, index):
        """
        """
        del self.pool[index]
    def __len__(self):
        """
        """
        return len(self.pool)
    def __iter__(self):
        """
        """
        return iter(self.pool)
    def iterAttr(self, *attr):
        """
        """
        if len(attr) == 1:
            for x in self:
                yield getattr(x, attr[0])
        else:
            for x in self:
                yield tuple(map(lambda ga: getattr(x, ga), attr))
    def shuffle(self):
        """
        """
        random.shuffle(self.pool)
    def reverse(self):
        """
        """
        self.pool.reverse()
    def sortBy(self, *attr):
        """
        """
        self.pool.sort(lambda x, y: compoundCompare(x, y, *attr))

class ReposList:
    """
    """
    def __init__(self, repos = None, lst = None):
        """
        """
        if repos:
            self.repos = repos
        else:
            self.repos = pyepl.repository.mainRepository
        if lst:
            self.lst = lst
        else:
            self.lst = []
    def __len__(self):
        """
        """
        return len(self.lst)
    def __add__(self, other):
        """
        """
        return ReposList(self.repos, self.lst + other.lst)
    def __contains__(self, other):
        """
        """
        for x in self:
            if x == other:
                return True
        return False
    def __delitem__(self, index):
        """
        """
        del self.lst[index]
    def __cmp__(self, other):
        """
        """
        for n in xrange(min(len(self), len(other))):
            r = cmp(self[n], other[n])
            if r != 0:
                return r
        return 0
    def __iadd__(self, other):
        """
        """
        for x in other:
            self.append(x)
    def __getitem__(self, index):
        """
        """
        if isinstance(index, slice):
            return map(lambda c: c(), self.lst[index])
        else:
            return self.lst[index]()
    def __setitem__(self, index, x):
        """
        """
        if isinstance(index, slice):
            self.lst[index] = map(lambda i: ReposRef(self.repos, i), x)
        else:
            self.lst[index] = ReposRef(self.repos, x)
    def append(self, obj):
        """
        """
        self.lst.append(ReposRef(self.repos, obj))
    def count(self, obj):
        """
        """
        c = 0
        for x in self.lst:
            if x.name == self.repos.getID(obj):
                c += 1
        return c
    def extend(self, l):
        self += l
    def index(self, obj, start = None, stop = None):
        """
        """
        for n in xrange(start, stop):
            if self.lst[n].name == self.repos.getID(obj):
                return n
        return -1
    def insert(self, index, obj):
        """
        """
        self.lst.insert(index, ReposRef(self.repos, obj))
    def pop(self, n = None):
        """
        """
        return self.lst.pop(n)()
    def remove(self, obj):
        """
        """
        del self.lst[self.find(obj)]
    def reverse(self):
        """
        """
        self.lst.reverse()
    def sort(self, cmpfunc = None):
        """
        """
        if not cmpfunc:
            cmpfunc = cmp
        self.lst.sort(lambda x, y: cmpfunc(x(), y()))
