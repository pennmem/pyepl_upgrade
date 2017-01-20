# PyEPL: __init__.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
PyEPL (Python Experiment Programming Library) is a package meant for
programming psychology experiments.
"""

import hardware
import timing
import display
import eeg
import keyboard
import joystick
import sound
import textlog
import stimulus
import transarchive
import repository
import pool
import vr
import os

from version import vstr as __version__

initialized = False

def initialize(**options):
    """
    Prepare the PyEPL repository and hardware interfaces for use.
    """
    global initialized
    if not initialized:
        initialized = True
        hardware.initialize(**options)

def finalize():
    """
    Cleanly shut down the PyEPL repository and hardware interfaces.
    """
    global initialized
    if initialized:
        hardware.finalize()
        initialized = False
