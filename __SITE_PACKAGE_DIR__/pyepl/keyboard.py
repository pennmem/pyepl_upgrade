# PyEPL: keyboard.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
The module provides access to the keyboard.
"""

import weakref
from textlog import LogTrack
from base import UniquelyConstructed
import hardware
import mechinput
import timing
import types

class Key(UniquelyConstructed, mechinput.Button):
    """
    Button representing a keyboard key.
    """
    waiting = []
    def __uinit__(self, keyname):
        """
        Construct Key from keyname.
        """
        mechinput.Button.__init__(self, keyname)
        self.keyname = keyname
        track = KeyTrack.lastInstance()
        if track:
            track.assignButton(self, keyname)
        else:
            Key.waiting.append(self)
    def __setstate__(self, state):
        """
        Attach to KeyTrack upon unpickling.
        """
        self.__dict__.update(state)
        track = KeyTrack.lastInstance()
        if track:
            track.assignButton(self, self.keyname)
        else:
            Key.waiting.append(self)
    def __getstate__(self):
        """
        Don't let pickle try and save the track that the key is
        associated with.
        """
        d = self.__dict__.copy()
        try:
            del d["track"]
        except KeyError:
            pass
        return d

class KeyTrack(LogTrack):
    """
    A Track for keyboard input.
    """
    trackTypeName = "KeyTrack"
    logExtension = ".keylog"
    def __init__(self, basename, archive = None, autoStart = True):        
        """
        Create the KeyTrack.

        INPUT ARGS:
          basename- The name of the log.
          archive- Directory to put the log.
          autoStart- Whether to automatically start the service
                     and logging.

        """
        LogTrack.__init__(self, basename, archive, autoStart)
        self.keys = weakref.WeakValueDictionary()
        for k in Key.waiting:
            self.assignButton(k, k.keyname)
        Key.waiting = []
    def startService(self):
        """
        Start the KeyTrack service.
        """
        hardware.setKeyboardCallback(self.callback)
    def stopService(self):
        """
        Stop the KeyTrack service
        """
        hardware.setKeyboardCallback(None)
    def key(self, keyname):
        """
        Return a Button object mapped to the named key.
        """
        return Key(keyname)
    def assignButton(self, button, keyname):
        """
        Trigger button for all events for the indicated key.  Binds
        the button object to the KeyTrack.

        INPUT ARGS:
          button- Button object to bind.
          keyname- Key to bind the button to.
        """
        keyval = hardware.nameToKey(keyname)
        if self.keys.has_key(keyval):
            raise ValueError, "Key already bound."
        self.keys[keyval] = button
    def keyChooser(self, *keys):
        """
        Return a ButtonChooser object for the specified keys.  If
        there are no keys specified, then return  all keys.

        INPUT ARGS:
          *keys- The names of keys you want to look up.
          
        """
        allkeys = []
        if keys:
            # add specified keys
            for keyname in keys:
		allkeys.append(self.key(keyname))
        else:
            # get all keys
            for keyname in hardware.keyNames():
                allkeys.append(self.key(keyname))

        # make button chooser and return
        return mechinput.ButtonChooser(*allkeys)
        #return allkeys
    
    def callback(self, k, pressed, timestamp):
        """
        This callback is called for every keyboard event and
        precipitates all pyEPL keyboard input.
        """
        if pressed:
            self.logMessage("P\t%s" % hardware.keyToName(k), timestamp)
        else:
            self.logMessage("R\t%s" % hardware.keyToName(k), timestamp)
        try:
            self.keys[k].setPressed(pressed, timestamp)
        except KeyError:
            pass
