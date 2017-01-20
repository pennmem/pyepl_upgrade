# PyEPL: stimulus.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
The stimulus class is in here.
"""

class Stimulus:
    """
    Base class that is foundation for presentable stimuli.
    """
    def present(self, clk = None, duration = None, jitter = None, bc = None, minDuration = None):
        """
        Method, which must be overridden for each stimulus class
        """
        pass
