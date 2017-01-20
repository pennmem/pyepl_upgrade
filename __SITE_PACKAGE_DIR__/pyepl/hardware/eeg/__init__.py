# PyEPL: hardware/eeg/__init__.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

from scalp import shmAttached, shmAttach, shmDetach, recStart, recStop, getOffset, EPLScalpEEGException

import sys

if sys.platform=='darwin':
    #from pulse import awCard, AWCException, LabJack, EPLPulseEEGException
    from pulse import LabJack, EPLPulseEEGException
else:
    from pulse import Parallel
    # from pulse import openPort, closePort, setState, setSignal, EPLPulseEEGException

def initialize(**options):
    """
    """
    pass

def finalize():
    """
    """
    from pyepl.eeg import EEGTrack
    et = EEGTrack.lastInstance()
    if not et is None:
        et.stopService()
