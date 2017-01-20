# PyEPL: textlog.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides a way to easily keep event logs.
"""

from base import Track
from exceptions import EPLFatalError
import timing
import os

# import exputils is at the bottom to fix import errors

class LogTrack(Track):
    """
    Respresents a textual event log.
    """
    trackTypeName = "LogTrack"
    logExtension = ".log"
    def __init__(self, basename, archive = None, autoStart = True):
        """
        """
        # Make sure we have an archive
        if not archive: 
            if not exputils.session:
                raise EPLFatalError("Log cannot be created without a subject archive.  An archive must either be passed as 2nd argument to constructor, or be a non-null referent of exputils.session.")
            archive = exputils.session
        
        self.dataFile = archive.createFile(basename + self.__class__.logExtension)
        self.logall = False

        # see if start service and logging
        if autoStart:
            self.startService()
            self.startLogging()
    def __iter__(self):
        """
        Iterate through (timestamp, withinTick, text)s of the messages
        in the log chronologically.  Not thread-safe!
        """
        wt = -1
        last_ts = -1
        filepos = 0
        while True:
            self.dataFile.seek(filepos)
            line = self.dataFile.readline().strip()
            filepos = self.dataFile.tell()
            if line == "":
                return
            tab = line.find("\t")
            ts = long(line[:tab])
            tab2 = line.find("\t", tab + 1)
            ml = long(line[tab + 1:tab2])
            txt = line[tab2 + 1:]
            if ts == last_ts:
                wt += 1
            else:
                wt = 0
                last_ts = ts
            yield (ts, ml), wt, txt
    def newTarget(self, archive):
        """
        Switch to a new archive location for this log.
        """
        waslogging = self.logall
        self.stopLogging()
        self.dataFile = archive.createFile(os.path.basename(self.dataFile.name))
        if waslogging:
            self.startLogging()
    def startLogging(self):
        """
        Begin logging.
        """
        if not self.logall:
            self.logall = True
            self.logMessage("B\tLogging Begins")
    def stopLogging(self):
        """
        Stop logging.
        """
        if self.logall:
            self.logMessage("E\tLogging Ends")
            self.logall = False
            self.dataFile.flush()
    def logMessage(self, message, timestamp = None):
        """
        Add message to log.

        INPUT ARGS:
        message- String to add to log.
        timestamp- Timestamp for this log entry.  If this is None,
        then the current time used as the timestamp.
        """
        if self.logall:
            if isinstance(timestamp, exputils.PresentationClock):
                timestamp = (timestamp.get(), 0L)
            elif timestamp is None:
                timestamp = (timing.now(), 0L)
            elif not isinstance(timestamp, tuple):
                timestamp = (timestamp, 0L)
            self.dataFile.seek(0, 2) # seek to end of file
            self.dataFile.write("%s\t%s\t%s\n" % (timestamp[0], timestamp[1], message))

    def flush(self):
        """
        Ensures that this log's data is entirely written to disk.
        """
        self.dataFile.flush()

import exputils  # we do this afterward because of "import from" dependencies
