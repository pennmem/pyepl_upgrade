# PyEPL: virtualtrack.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

from base import Track
import re
import itertools

class VirtualTrack(Track):
    """
    This class allows the creation of tracks which combine information
    from other tracks.
    """
    logExtension = ".vtrack"
    def __init__(self, *columns):
        """
        Each argument represents a column that will be represented in
        the VirtualTrack.  They may have the following formats:

        1. A 2-tuple of source track and source column number.
             eg. (audio, 1)
             
        2. A 3-tuple, as in #1, with the last element being a regular
           expression against which the full original row will be
           compared.  The row will contribute a value to this column
           if and only in the regular expression matches.
             eg. (audio,2,"^BEEP\t")
             
        3. A 4-tuple, as in #2, with the last element being a default
           value to be used in the case that no matching value is
           available from the source track.  If the regular expression
           is None, no regular expression is used and the defaults
           value is still used for other circumstances in which no
           value is available.  Without this paremeter, an empty
           string is used.
             eg. (audio,3,"^BEEP\t","no match")
        4. A callable accepting a PyEPL millisecond time and returning
           a 2-tuple of a value for the column at the provided
           millisecond time and a maximum latency for the accuracy of
           that value.  This type of column is valued only when at
           least one other column is valued.
             eg. eeg.offset
        
        Example: VirtualTrack(eeg.offset, (audio, 1, "^BEEP\t"), (audio, 2, "^BEEP\t"))

        INPUT ARGS:
          columns- A variable number of virtual column specifiers as
                   described in items 1-4 above.
        """

        Track.__init__(self)
        self.columns = columns
    def getNextVal(self, column, citer):
        """
        Internal use only!
        """
        for x in citer:
            if len(column) >= 3 and not column[2] is None and not re.compile(column[2]).search(x[2]):
                continue
            return (x[0], x[1], x[2].split("\t")[column[1]])
        return None
    def __iter__(self):
        """
        Iterate chronologically through 3-tuples of marked event
        times, within tick order numbers, texts for all components.

        OUTPUTS:
          g- a generator for each of the entries in the virtual track.
          
        """
        iters = []
        nextvals = []
        for column in self.columns:
            if isinstance(column, tuple):
                i = iter(column[0])
                iters.append(i)
                nextvals.append(self.getNextVal(column, i))
            else:
                iters.append(None)
                nextvals.append(None)
        wt = 0
        lasttick = None
        while True:
            earliest = None
            for nextval in nextvals:
                if not nextval is None and (nextval[0][0] < earliest or earliest is None):
                    earliest = nextval[0][0]
            if earliest is None:
                return
            if earliest == lasttick:
                wt += 1
            else:
                wt = 0
                lasttick = earliest
            columnvals = []
            maxlat = 0
            for n, (column, nextval, citer) in enumerate(itertools.izip(self.columns, nextvals, iters)):
                if isinstance(column, tuple):
                    if not nextval is None and nextval[0][0] == earliest:
                        lat = nextval[0][1]
                        columnvals.append(str(nextval[2]))
                        nextvals[n] = self.getNextVal(column, citer)
                    else:
                        lat = 0
                        if len(column) == 4:
                            columnvals.append(column[3])
                        else:
                            columnvals.append("")
                else:
                    value, lat = column(earliest)
                    columnvals.append(str(value))
                if lat > maxlat:
                    maxlat = lat
            yield ((earliest, maxlat), wt, "\t".join(columnvals))
