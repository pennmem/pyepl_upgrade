# PyEPL: base.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module defines useful base classes for objects to be stored in a
repository.
"""

import pyepl.exceptions
from transarchive import Archive
import weakref
import os

class CarveError(Exception):
    """
    """
    def __init__(self, obj):
        """
        """
        self.obj = obj
    def __str__(self):
        """
        """
        return "Attempt to modify a carved Carvable: %r" % self.obj

class Carvable:
    """
    This is a super-class for all objects that can be "carved in
    stone".  In other words, they can be solidified so that their
    contents can never be changed again.
    """
    def __init__(self):
        """
        """
        self.carved_in_stone = False
    def carve(self):
        """
        """
        self.carved_in_stone = True
    def isCarved(self):
        """
        """
        return self.carved_in_stone
    def aboutToChange(self):
        """
        """
        if self.carved_in_stone:
            raise CarveError(self)

class Registry(type):
    """
    Metaclass for classes to be registered for common services.
    """
    extensionRegistry = {}
    encodeRegistry = {}
    decodeRegistry = {}
    trackTypes = {}
    def __new__(cls, name, bases, dict):
        """
        """
        t = type.__new__(cls, name, bases, dict)
        if hasattr(t, "logExtension"):
            Registry.extensionRegistry[t.logExtension] = t
        if hasattr(t, "trackTypeName"):
            Registry.trackTypes[t.trackTypeName] = t
        return t
    def loadFile(filename):
        """
        Load the indicated file using the correct registered class.
        Return the resulting object.
        """
        cls = Registry.extensionRegistry(os.path.splitext(filename))
        directory, filename = os.path.split(filename)
        return cls(Archive(directory), os.path.splitext(filename)[0])
    loadFile = staticmethod(loadFile)

class Registered(object):
    """
    Base instance of Registry metaclass.
    """
    __metaclass__ = Registry

class MediaFile(Registered):
    """
    """
    def load(self):  # To be overridden
        """
        """
        pass
    def unload(self):  # To be overridden
        """
        """
        pass
    def isLoaded(self):  # To be overridden
        """
        """
        return True
    def loadedCall(self, f, *targs, **dargs):
        """
        """
        if self.isLoaded():
            return f(*targs, **dargs)
        self.load()
        r = f(*targs, **dargs)
        return r

class Track(Registered):
    """
    This is a super-class for all formats that have values varying
    with time.  These include sound, video, eeg, and textual logging.
    """
    def __new__(cls, *targs, **dargs):
        """
        Call Format constructor and then set most recently constructed
        instance.
        """
        self = object.__new__(cls, *targs, **dargs)
        self.__class__.last_instance = weakref.ref(self)
        return self
    def __iter__(self):
        """
        Generator to iterate through marked events in the track.
        Generates 3-tuples of (time stamps, maximum latencies), within
        tick order numbers, texts.
        """
        return iter(lambda: None, None) # No marked events by default (better way?)
    def __del__(self):
        """
        Clean up the Track
        """
        self.stopLogging()
        self.flush()
        self.stopService()
    def export(self, archive, basename):
        """
        Iterate through marked events writing string form to file.
        """
        filename = basename + self.__class__.logExtension
        of = archive.createFile(filename)
        for (timestamp, maxlat), withintick, txt in self:
            of.write("%s\t%s\t%s\n" % (timestamp, maxlat, txt))
        return filename
    def flush(self):  # To be overridden
        """
        """
        pass
    def startLogging(self):  # To be overridden
        """
        """
        pass
    def stopLogging(self):  # To be overridden
        """
        """
        pass
    def startService(self):  # To be overridden
        """
        """
        pass
    def stopService(self):  # To be overridden
        """
        """
        pass
    def doAction(self, dotime, name, context):  # To be overridden
        """
        """
        pass
    def getActions(self):  # To be overridden
        """
        """
        pass
    def lastInstance(cls):
        """
        Return the last constructed instance of this class (this class
        refers to the class it's called on, not just Track.  If last
        instance does not exist, return None.
        """
        try:
            return cls.__dict__["last_instance"]()
        except KeyError:
            return None
    lastInstance = classmethod(lastInstance)

class MetaUniquelyConstructed(type):
    """
    """
    def __new__(cls, name, bases, dict):
        """
        """
        dict["loaded"] = weakref.WeakValueDictionary()
        return type.__new__(cls, name, bases, dict)

class UniquelyConstructed(object):
    """
    """
    __metaclass__ = MetaUniquelyConstructed
    def __new__(cls, *targs, **dargs):
        """
        """
        try:
            return cls.loaded[(targs, tuple(dargs.items()))]
        except KeyError:
            return object.__new__(cls, *targs, **dargs)
    def __init__(self, *targs, **dargs):
        """
        """
        if not self in self.__class__.loaded.values():
            self.__class__.loaded[(targs, tuple(dargs.items()))] = self
            self.__uinit__(*targs, **dargs)
    def __uinit__(self, *targs, **dargs):  # to be overridden
        """
        """
        pass
