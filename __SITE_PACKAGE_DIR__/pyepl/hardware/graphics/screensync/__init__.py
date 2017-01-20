# PyEPL: hardware/graphics/screensync/__init__.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This package implements blocking the monitor's Vertical Blanking Loop.

"""
import os

def initialize(**options):
    """
    """
    pass

def finalize():
    """
    """
    pass

def linuxSetRefreshBlock(tf):
    if tf:
        val = "1"
    else:
        val = "0"

    # Set for nVidia linux
    os.environ["__GL_SYNC_TO_VBLANK"] = val
    # Set for recent linux Mesa DRI Radeon
    os.environ["LIBGL_SYNC_REFRESH"] = val

if os.uname()[0]=='Darwin':
    import _refreshBlock
    setRefreshBlock = _refreshBlock.sync_swap
