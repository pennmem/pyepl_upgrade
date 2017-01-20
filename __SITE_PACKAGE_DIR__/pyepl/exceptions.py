# PyEPL: exceptions.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module defines some base exceptions for PyEPL.
"""

import warnings

class EPLException(Exception):
    """
    Base exception class for PyEPL.
    """
    def __init__(self, desc):
        """
        Initialize exception with a description.
        """
        self.desc = desc
    def __str__(self):
        """
        Get a string representation of this exception.
        """
        return "EPL Exception: %s" % self.desc

class EPLError(EPLException):
    """
    Base class for PyEPL errors (i.e. normal execution cannot
    continue).
    """
    def __str__(self):
        """
        Get a string representation of this error.
        """
        return "EPL Error: %s" % self.desc

def eplWarn(message, category = UserWarning, stackLevel = 1):
    """
    Issue a warning.  Execution continues normally.
    """
    warnings.warn("EPL Warning: %s" % message, category, stackLevel + 1)

class EPLFatalError(EPLError):
    """
    An error so serious that execution cannot continue at all.
    """
    def __str__(self):
        """
        Get a string representation of this error.
        """
        return "EPL FATAL ERROR: %s" % self.desc

class BadFileExtension(EPLError):
    """
    Error indicating that a filename extension was not understood.
    """
    def __init__(self, ext):
        """
        Get a string representation of this error.
        """
        EPLError.__init__(self, "The file extension %s is not recognized in context." % ext);
