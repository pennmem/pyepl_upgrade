# PyEPL: pool.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides tools for manipulating collections of stimuli.
"""

import sound
import display
from exceptions import BadFileExtension
from base import MediaFile
import os
import copy
import random
import itertools

IMAGE_EXTS = ["bmp", "png", "jpg", "jpeg", "tif", "xpm"]
TEXT_EXTS = ["txt"]

def compoundCompare(x, y, *attr):
    """
    Loops through the specified attributes for x and y and returns the
    result of comparing them.  Will return the first time the
    comparison is not equal to zero.

    INPUT ARGS:
      x and y- Two objects to compare.
      *attr- List of attributes to compare.
    """
    for a in attr:
        r = cmp(getattr(x, a), getattr(y, a))
        if r != 0:
            return r
    return 0

class PoolDict(dict):
    """
    Dictionary where you can access the values as attributes.
    """
    def copy(self):
        """
        Like the copy method of dict, but returns a PoolDict.
        """
        return PoolDict(self)
    def __getattr__(self, name):
        """
        Get a value from the dictionary as an attribute.
        INPUT ARGS:
          name- name of the dictionary entry
        OUTPUT ARGS:
          val- value of that entry.

        """
        try:
            return self[name]
        except KeyError:
            raise AttributeError, name
    def __setattr__(self, name, value):
        """
        Set a value in the dictionary as an attribute.
        INPUT ARGS:
          name- name of the dictionary entry
          val- value of that entry.
        """
        self[name] = value
    def __delattr__(self, name):
        """
        Delete a value from the dictionary as an attribute.
        INPUT ARGS:
          name- name of the dictionary entry to delete        
        """
        try:
            del self[name]
        except KeyError:
            raise AttributeError, name
    def __eq__(self, other):
        """
        PoolDicts are equal if they are the same object OR, it they
        have the same "name" attribute.
        """
        try:
            return self.name == other.name
        except AttributeError:
            try:
                return dict.__eq__(other)
            except TypeError:
                return False

class Pool(list):
    """
    An ordered collection of PoolDicts.
    """
    def __init__(self, *tdicts, **ddicts):
        """
        Create the Pool.  The first argument can optionally be a
        string containing a path to a file or directory from which
        stimuli should be read.  All remaining positional arguments
        will initially populate the Pool in order.  They will be
        followed by the values of all keyword arguments, where the
        name of each keyword argument has been included in the
        corresponding value as the attribute "name".

        INPUT ARGS:
          tdicts- PoolDicts to initially populate the pool, excepting
          the first item, if it is a string, in which case it will be
          used as a path to a file or directory from which to read
          stimuli
          ddicts- PoolDicts to initially populate the pool where the
          name attributes will be taken from the names of the keyword
          arguments
        """
        list.__init__(self)
        self.SOUND_EXTS = sound.formatDict.keys()
        if len(tdicts) and isinstance(tdicts[0], str):
            self.loadFromSourcePath(tdicts[0])
            tdicts = tdicts[1:]
        for d in tdicts:
            list.append(self, PoolDict(d))
        for name, d in ddicts.iteritems():
            d = PoolDict(d)
            d.name = name
            list.append(self, d)
	
    def loadFromSourcePath(self, sourcepath):
        """
        """
        if os.path.isdir(sourcepath):
            # is a directory, loop over files
            for stimfile in os.listdir(sourcepath):
                # strip off filename and extension
                name, ext = os.path.splitext(stimfile)
                ext = ext.lower()
                if not name or not ext:
                    continue
                # process based on extension
		ext = ext[1:]
                try:
                    stimobj = self.findBy(name = name)
                except LookupError:
                    stimobj = self.append(name = name)
                if ext == "dummy":
                    pass
                elif ext in self.SOUND_EXTS:
                    stimobj.content = sound.FileAudioClip(os.path.abspath(os.path.join(sourcepath, stimfile)), format=ext)
                elif ext in IMAGE_EXTS:
                    stimobj.content = display.Image(os.path.abspath(os.path.join(sourcepath, stimfile)))
                elif ext in TEXT_EXTS:
                    # load file as a textpool
                    #stimobj.content = display.Text(open(os.path.abspath(os.path.join(sourcepath, stimfile))).read())
                    stimobj.content = TextPool(os.path.abspath(os.path.join(sourcepath,stimfile)))
                else:
		    raise BadFileExtension, ext
        else:
            # assumes text file
            for line in open(sourcepath, "r"):
                textval = line.strip()
                self.append(name = textval, content = display.Text(textval))
                
    def append(self, actualpooldict = None, **items):
        """
        Append a pooldir to a pool, returning the new one.
        INPUT ARGS:
          item- the pooldir to add to the pool.
        """
        if actualpooldict:
            if not isinstance(actualpooldict, PoolDict):
                raise TypeError, "Pools may only contain PoolDicts"
            if len(items):
                items.update(actualpooldict)
                r = PoolDict(**items)
            else:
                r = actualpooldict
        else:
            r = PoolDict(**items)
        list.append(self, r)
        return r
    def insert(self, n, actualpooldict = None, **items):
        """
        Inserts a pooldir into the pool at a specified position.
        INPUT ARGS:
          n- the position in pool to add the specified pooldir
          items- the pooldir to add to the pool.

        """
        if actualpooldict:
            if len(items):
                items.update(actualpooldict)
                r = PoolDict(**items)
            else:
                r = actualpooldict
        else:
            r = PoolDict(**items)
        list.insert(self, n, r)
        return r
    def extend(self, p):
        """
        Adds the contents of another pool to this pool's contents.
        INPUT ARGS:
          p- the new pool whose contents will be added to this pool        
        """
        l = list(p)
        for x in l:
            if not isinstance(x, PoolDict):
                raise ValueError, "Pools may only contain PoolDicts"
        list.extend(self, l)
    def uniqueExtend(self, other):
        """
        Like extend, but do not append items when an equal item is
        already in the Pool.
        """
        # for each item in the source list...
        for x in other:
            # ...check if it's already in the target list
            if not x in self:
                if not isinstance(x, PoolDict):
                    raise ValueError, "Pools may only contain PoolDicts"
                
                # if not, add it
                self.append(x)
    def __getitem__(self, index):
        """
        Retrieves the PoolDir(s) at the specified index.  If a slice
        of indices is specified, multiple PoolDirs are returned in the
        form of another pool.

        INPUT ARGS:
          index- the index of the desired PoolDir.  This can be a
            slice (referencing multiple PoolDirs).
        OUTPUT ARGS:
          The PoolDir at the specified index.  If the user specified a
          slice of indices, then the PoolDirs for those indices are
          returned as a single Pool object        
        """
        r = list.__getitem__(self, index)
        if isinstance(r, list):
            return Pool(*r)
        return r
    def __getslice__(self, i, j):
        """
        """
        return Pool(*list.__getslice__(self, i, j))
    def __setitem__(self, index, value):
        """
        Sets the value of the PoolDir at the specified index
        INPUT ARGS:
          index- index of Pooldir to modify
          value- PoolDir to be set at that position.
        """
        if isinstance(index, slice):
            for v in value:
                if not isinstance(v, PoolDict):
                    raise TypeError, "Pools may only contain PoolDicts"
        if not isinstance(value, PoolDict):
            raise TypeError, "Pools may only contain PoolDicts"
        list.__setitem__(self, index, value)
    def __setslice__(self, i, j, values):
        """

        """
        for v in values:
            if not isinstance(v, PoolDict):
                raise TypeError, "Pools may only contain PoolDicts"
        list.__setslice__(self, i, j, values)
    def __add__(self, other):
        """
        """
        return Pool(*list.__add__(self, other))
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
        Shuffles the order of the PoolDirs in this pool
        """
        random.shuffle(self)
    def randomChoice(self):
        """
        Return a random element from the Pool.
        """
        return random.choice(self)
    def sample(self, k = None):
        """
        Returns a random non-repeating sample of the PoolDirs in this pool.
        INPUT ARGS:
          k- number of samples requested. (if omitted, k is set to the number of items in the pool)
        OUTPUT ARGS:
          sample- a Pool object containing a random sample of the elements in the Pool        
        """
        if k is None:
            k = len(self)
        return Pool(*random.sample(self, k))
    def sortBy(self, *attr):
        """
        Orders the PoolDirs in the Pool by the specified attribute(s).
          attr- A list of strings containing the names of the
          attributes to sort the PoolDirs by.  The PoolDirs are sorted
          in the order the attributes are specified in.        
        """
        list.sort(self, lambda x, y: compoundCompare(x, y, *attr))
    def sort(self):
        """
        Sort the stimuli by the name attribute.
        """
        self.sortBy("name")
    def iterFindBy(self, **attrvalues):
        """
        Generate all PoolDicts in this Pool for which the pairings
        between name and value given in this call's keyword arguments
        are all true.
        """
        for d in self:
            for name, value in attrvalues.iteritems():
                try:
                    if getattr(d, name) != value:
                        break
                except AttributeError:
                    break
            else:
                yield d
    def findAllBy(self, **attrvalues):
        """
        Return a Pool of the results from iterFindBy.
        """
        return Pool(*self.iterFindBy(**attrvalues))
    def findBy(self, **attrvalues):
        """
        Return the first PoolDict found by a call to iterFindBy with
        the same arguments.  Raises a LookupError, if no match is
        found.
        """
        try:
            return self.iterFindBy(**attrvalues).next()
        except StopIteration:
            raise LookupError, "No matching PoolDict found (%r)" % attrvalues
    def removeBy(self, **attrvalues):
        """
        Remove all PoolDicts in this Pool for which the pairings
        between name and value given in this call's keyword arguments
        are all true.
        """
        removelist = []
        for d in self.iterFindBy(**attrvalues):
            removelist.append(d)
        for d in removelist:
            self.remove(d)
    def makeTexts(self, sourceattr = "name", targetattr = "text", font = None, size = None, color = None):
        """
        For every PoolDict in this Pool which has an attribute named
        as the string sourceattr, create a new attribute named as the
        string targetattr whose value is a Text object made a string
        version of the value of the existing attribute.
        """
        for d in self:
            try:
                setattr(d, targetattr,
                        display.Text(str(getattr(d, sourceattr)), font = font, size = size, color = color))
            except AttributeError:
                pass
    def middleDepthCopy(self):
        """
        Return a copy of this Pool containing shallow copies of the
        contained PoolDicts.
        """
        r = Pool()
        for d in self:
            r.append(d.copy())
        return r

class ImagePool(Pool):
    """
    Pool subclass for images.
    """
    def __init__(self, dirname, xscale=None, yscale=None, *tdicts, **ddicts):
        """
        Constructor assumes it will at least receive a directory from
        which to load images, and optionally scale factor(s) to apply
        to all images in the directory.
        """
        list.__init__(self)
        self.loadFromSourcePath(dirname, xscale, yscale)
        for d in tdicts:
            list.append(self, PoolDict(d))
        for name, d in ddicts.iteritems():
            d = PoolDict(d)
            d.name = name
            list.append(self, d)
    def loadFromSourcePath(self, sourcepath, xscale, yscale):
        """
        """
        if os.path.isdir(sourcepath):
            for stimfile in os.listdir(sourcepath):
                name, ext = os.path.splitext(stimfile)
                ext = ext.lower()
                if not name or not ext:
                    continue
                try:
                    stimobj = self.findBy(name = name)
                except LookupError:
                    stimobj = self.append(name = name)
                if ext == ".dummy":
                    pass
                elif ext[1:] in IMAGE_EXTS:
                    if xscale:
                        if yscale:
                            stimobj.content = display.Image(os.path.abspath(os.path.join(sourcepath, stimfile)), xscale, yscale)
                        else:
                            stimobj.content = display.Image(os.path.abspath(os.path.join(sourcepath, stimfile)), xscale, xscale)
                    elif yscale:
                        stimobj.content = display.Image(os.path.abspath(os.path.join(sourcepath, stimfile)), yscale, yscale)
                    else:
                        stimobj.content = display.Image(os.path.abspath(os.path.join(sourcepath, stimfile)))
                else:
                    raise BadFileExtension, ext
        else:
            raise ValueError("Directory %s not found." % sourcepath)

class TextPool(Pool):
    """
    Pool subclass for text.
    """
    def __init__(self, fileordir, size=None, color=None, font=None, *tdicts, **ddicts):
        """
        Constructor assumes it will at least receive a directory from
        which to load images, and optionally scale factor(s) to apply
        to all images in the directory.
        """
        list.__init__(self)
        self.loadFromSourcePath(fileordir, size, color, font)
        for d in tdicts:
            list.append(self, PoolDict(d))
        for name, d in ddicts.iteritems():
            d = PoolDict(d)
            d.name = name
            list.append(self, d)
    def loadFromSourcePath(self, sourcepath, size, color, font):
        """
        """
        if os.path.isdir(sourcepath):
            for stimfile in os.listdir(sourcepath):
                name, ext = os.path.splitext(stimfile)
                ext = ext.lower()
                if not name or not ext:
                    continue
                try:
                    stimobj = self.findBy(name = name)
                except LookupError:
                    stimobj = self.append(name = name)
                if ext == ".dummy":
                    pass
                elif ext[1:] in TEXT_EXTS:
                    # load text file as TextPool
                    stimobj.content = TextPool(os.path.abspath(os.path.join(sourcepath,stimfile)))
                    #stimobj.content = display.Text(open(os.path.abspath(os.path.join(sourcepath, stimfile))).read(), size=size, color=color, font=font)
                else:
                    raise BadFileExtension, ext
        else:
            for line in open(sourcepath, "r"):
                textval = line.strip()
                self.append(name = textval,
                            content = display.Text(textval, size=size, color=color, font=font))

class SoundPool(Pool):
    """
    Pool subclass for soundfiles.
    """
    def __init__(self, dirname, *tdicts, **ddicts):
        """
        """
	self.SOUND_EXTS = sound.formatDict.keys()
	self.soundArgs = copy.copy(sound.defaultFileSettings)
	# always set format based of file extensions:
	soundFields = self.soundArgs.keys()
	del self.soundArgs['format']
        list.__init__(self)
        self.loadFromSourcePath(dirname)
        for d in tdicts:
            list.append(self, PoolDict(d))
        for name, d in ddicts.iteritems():
	    print name
	    print soundFields
	    if name not in soundFields:
		d = PoolDict(d)
		d.name = name
		list.append(self, d)
	    else:
		self.soundArgs[name] = d
    def loadFromSourcePath(self, sourcepath):
        """
        """
        if os.path.isdir(sourcepath):
            for stimfile in os.listdir(sourcepath):
                name, ext = os.path.splitext(stimfile)
                ext = ext.lower()
                if not name or not ext:
                    continue
		ext = ext[1:]
                try:
                    stimobj = self.findBy(name = name)
                except LookupError:
                    stimobj = self.append(name = name)
                if ext == "dummy":
                    pass
                elif ext in self.SOUND_EXTS:
		    self.soundArgs['format'] = ext
                    stimobj.content = sound.FileAudioClip(os.path.abspath(os.path.join(sourcepath, stimfile)), self.soundArgs)
                else:
                    raise BadFileExtension, ext
        else:
            raise ValueError("Directory %s not found." % sourcepath)
