# PyEPL: hardware/rt/__init__.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This package implements realtime functions.
"""
import sys
if sys.platform=='darwin':
    from realtime import *      
else:
    from linux_realtime import *

def initialize(**options):
    """
    """
    pass

def finalize():
    """
    """
    pass
