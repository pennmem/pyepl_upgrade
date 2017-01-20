# PyEPL: ./transarchive.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.
# Revision 1.5  2005/11/08 23:04:01  aaron
# log test
#

"""
Module for accessing heirarchical disk data.
"""

from pyepl.exceptions import BadFileExtension
import os
import shutil
import StringIO
from tempfile import TemporaryFile
import tarfile
import weakref

class AbstractArchive:
    """
    Abstract interface to heirarchical data storage (file systems).
    """
    def copyTo(self, arc):
        """
        Replicate contents within arc.
        """
        for name in self.listDir():
            if self.isFile(name):
                src = self.open(name)
                src.seek(0)
                trg = arc.createFile(name)
                trg.seek(0)
                trg.write(src.read())
            else:
                self.open(name).copyTo(arc.createDirectory(name))
    def listDir(self):
        """
        Return a list of filenames in this Archive.
        """
        pass #...
    def exists(self, name):
        """
        Return true if file exists.  Otherwise return False.
        """
        pass #...
    def isFile(self, name):
        """
        Return true if name specifies a file (not a directory).
        Otherwise return False.
        """
        pass #...
    def delete(self, name):
        """
        Delete named file or directory.
        """
        pass #...
    def open(self, name):
        """
        If the name specifies a file, return a file or file-like
        object (rw for non-compressed, r for compressed).  If it's a
        directory, return a new Archive object.
        """
        pass #...
    def createDirectory(self, name):
        """
        Create an empty directory.
        """
        pass #...
    def createFile(self, name):
        """
        Create an empty file.
        """
        pass #...

class VirtualArchive(AbstractArchive):
    """
    Class to represent a virtual directory.
    """
    def __init__(self):
        """
        Create empty virtual directory.
        """
        self.dir = {}
    def listDir(self):
        """
        Return a list of filenames in this Archive.
        """
        return self.dir.keys()
    def exists(self, name):
        """
        Return true if file exists.  Otherwise return False.
        """
        return name in self.dir.keys()
    def isFile(self, name):
        """
        Return true if name specifies a file (not a directory).
        Otherwise return False.
        """
        return isinstance(self.dir[name], StringIO.StringIO)
    def delete(self, name):
        """
        Delete named file or directory.
        """
        del self.dir[name]
    def open(self, name):
        """
        If the name specifies a file, return a file or file-like
        object (rw for non-compressed, r for compressed).  If it's a
        directory, return a new Archive object.
        """
        return self.dir[name]
    def createDirectory(self, name):
        """
        Create an empty directory.
        """
        x = SoftArchive()
        self.dir[name] = x
        return x
    def createFile(self, name):
        """
        create an emptry file.
        """
        x = StringIO.StringIO()
        self.dir[name] = x
        return x

class Archive(AbstractArchive):
    """
    Class to represent a physical directory.
    """
    def __init__(self, path):
        """
        Construct archive object from path.
        """
        path = os.path.abspath(path)
        if not os.path.exists(path):
            os.mkdir(path)
        self.path = path
    def listDir(self):
        """
        Return a list of filenames in this Archive.
        """
        return os.listdir(self.path)
    def exists(self, name):
        """
        Return true if file exists.  Otherwise return False.
        """
        return os.path.exists(self.fullPath(name))
    def isFile(self, name):
        """
        Return true if name specifies a file (not a directory).
        Otherwise return False.
        """
        return not os.path.isdir(self.fullPath(name))
    def delete(self, name):
        """
        Delete named file or directory.
        """
        fp = self.fullPath(name)
        if os.path.isdir(fp):
            shutil.rmtree(fp)
        else:
            os.remove(fp)
    def open(self, name):
        """
        If the name specifies a file, return a file or file-like
        object (rw for non-compressed, r for compressed).  If it's a
        directory, return a new Archive object.
        """
        p = self.fullPath(name)
        if os.path.isdir(p):
            return Archive(p)
        return open(p, "r+b")
    def fullPath(self, name = ""):
        """
        Return the absolute path of this archive.
        """
        return os.path.join(self.path, name)
    def createDirectory(self, name):
        """
        Create an empty directory.
        """
        if not self.exists(name):
            os.mkdir(self.fullPath(name))
        return self.open(name)
    def createFile(self, name):
        """
        create an emptry file.
        """
        if not self.exists(name):
            open(self.fullPath(name), "w")
        return open(self.fullPath(name), "r+b")

class TarredFile:
    """
    """
    def __init__(self, tarpath, arc):
        """
        """
        tf = TemporaryFile()
        self.tarpath = tarpath
        self.arc = arc
        self.stored_away = False
    def __getattr__(self, name):
        """
        """
        return getattr(self.tf, name)
    def store_away(self):
        """
        """
        if not self.stored_away:
            self.stored_away = True
            self.tf.seek(0, 2)
            ti = tarfile.TarInfo(self.tarpath)
            ti.size = self.tf.tell()
            self.tf.seek(0)
            self.arc.addfile(ti, self.tf)
    def __del__(self):
        """
        """
        self.store_away()
        del tf
    def close(self):
        """
        """
        self.store_away()
        tf.close()

class TarArchive(AbstractArchive):
    """
    """
    def __init__(self, filename, arc = None):
        """
        """
        if arc:
            self.arc = arc
            self.tarpath = filename
            return
        if os.path.exists(filename):
            self.arc = tarfile.open(filename, "r")
        else:
            if filename.endswith(".tar"):
                self.arc = tarfile.open(filename, "w")
            elif filename.endswith(".tgz") or filename.endswith(".tar.gz"):
                self.arc = tarfile.open(filename, "w:gz")
            elif filename.endswith(".tar.bz2"):
                self.arc = tarfile.open(filename, "w:bz2")
            else:
                raise BadFileExtension, "Tarfile with extension: %s" % os.path.splitext(filename)[1][1:].upper()
        self.tarpath = ""
        self.openned = weakref.WeakValueDictionary()
    def listDir(self):
        """
        Return a list of filenames in this Archive.
        """
        r = []
        tp = len(self.tarpath)
        for name in self.arc.getnames():
            if name.startswith(self.tarpath):
                r.append(name[tp:name.find("/", tp)])
        return r
    def exists(self, name):
        """
        Return true if file exists.  Otherwise return False.
        """
        try:
            self.arc.getmember(self.tarpath + name)
            return True
        except KeyError:
            return False
    def isFile(self, name):
        """
        Return true if name specifies a file (not a directory).
        Otherwise return False.
        """
        return self.arc.getmember(self.tarpath + name).isfile()
    def delete(self, name):
        """
        Delete named file or directory.
        """
        raise ValueError, "TarArchive does not support deletion."
    def open(self, name):
        """
        If the name specifies a file, return a file or file-like
        object (rw for non-compressed, r for compressed).  If it's a
        directory, return a new Archive object.
        """
        try:
            return self.openned[name]
        except KeyError:
            pass
        fn = self.tarpath + name
        ti = self.arc.getmember(fn)
        if ti.type == tarfile.DIRTYPE:
            return TarArchive(fn + "/", self.arc)
        r = self.arc.extractfile(ti)
        self.openned[name] = r
        return r
    def createDirectory(self, name):
        """
        Create an empty directory.
        """
        fn = self.tarpath + name
        ti = tarfile.TarInfo(fn)
        ti.type = tarfile.DIRTYPE
        self.arc.addfile(ti)
        r = TarArchive(fn + "/", self.arc)
        self.openned[name] = r
        return r
    def createFile(self, name):
        """
        Create an empty file.
        """
        r = TarredFile(self.tarpath + name, self.arc)
        self.openned[name] = r
        return r

def openArchive(filename):
    """
    """
    if filename.endswith(".tar") or filename.endswith(".tgz") or filename.endswith(".tar.gz") or filename.endswith(".tar.bz2"):
        return TarArchive(filename)
    else:
        return Archive(filename)
