# PyEPL: version.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
Version management module.
"""

from distutils.version import StrictVersion
from exceptions import EPLFatalError

## !!!!!
## MAKE SURE THIS MATCHES THE VERSION NUMBER IN pyepl/setup.py !!!
vstr = '1.1.2'
## !!!!!

pyeplVersion = StrictVersion(vstr)

def checkVersion(someString):
    """
    Check that the current pyepl Version >= argument string's version.
    """
    if not pyeplVersion >= StrictVersion(someString):
        raise EPLFatalError("This experiment requires at least PyEPL version %s, but currently only version %s is installed." % (someString, vstr))

def checkVersionRange(str1, str2):
    """
    Check that the current pyepl version is in the version-range described
    by the 2 argument strings.
    """
    if not (pyeplVersion >= StrictVersion(str1) and pyeplVersion <= StrictVersion(str2)):
        raise EPLFatalError("This experiment requires a PyEPL version between %s and %s, but currently %s is installed." % (str1, str2, vstr))
