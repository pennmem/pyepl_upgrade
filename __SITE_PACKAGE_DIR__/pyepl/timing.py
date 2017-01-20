# PyEPL: timing.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides high-level timing features.
"""

import hardware
import exputils

now = hardware.universal_time
timedCall = hardware.timedCall

def timedCall(t, f, *targs, **dargs):
    """
    At time t, call f with any remaining arguments.  Returns a 2-tuple
    of a timestamp for the time and maximum latency of the actual call
    to f, and the return value of the call.  If t is None or 0, the
    call is made immediately.

    INPUT ARGS:
      t- time at which to execute call.  This can be specified as an
         integer specifying a millisecond time to run,
         OR as a PresentationClock object.
      f- a callable to run at the specified time
      args- arguments to pass to f when it is called.
    
    """
    if isinstance(t, exputils.PresentationClock):
        return hardware.timedCall(t.get(), f, *targs, **dargs)
    return hardware.timedCall(t, f, *targs, **dargs)

delay = hardware.delay
wait = hardware.wait
