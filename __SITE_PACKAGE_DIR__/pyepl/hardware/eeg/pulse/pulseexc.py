# PyEPL: hardware/eeg/pulse/pulseexc.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

from pyepl.exceptions import EPLException

class EPLPulseEEGException(EPLException):
    def __init__(self, desc):
        self.desc = desc
    def __str__(self):
        return "EPL Pulse EEG Exception: %s" % self.desc
