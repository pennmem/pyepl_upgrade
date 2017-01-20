# PyEPL: mouse.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides access to the mouse.
"""

import weakref
from textlog import LogTrack
from base import UniquelyConstructed
import hardware
import mechinput
import timing

class MouseButton(UniquelyConstructed, mechinput.Button):
    """
    Button representing a mouse button.
    """
    waiting = []
    def __uinit__(self, buttonnum):
        """
        Construct MouseButton.
        INPUT ARGS:
          buttonnum- mouse button this object should correspond to
        """
        mechinput.Button.__init__(self, "Mouse button %d" % buttonnum)
        self.buttonnum = buttonnum
        track = MouseTrack.lastInstance()
        if track:
            track.assignButton(self, buttonnum)
        else:
            MouseButton.waiting.append(self)
    def __setstate__(self, state):
        """
        Attach to MouseTrack upon unpickling.
        """
        self.__dict__.update(state)
        track = MouseTrack.lastInstance()
        if track:
            track.assignButton(self, self.buttonnum)
        else:
            MouseButton.waiting.append(self)
    def __getstate__(self):
        """
        """
        d = self.__dict__.copy()
        try:
            del d["track"]
        except KeyError:
            pass
        return d

class MouseAxis(UniquelyConstructed, mechinput.Axis):
    """
    Axis representing a mouse axis.

    MouseAxis represents a mouse's position on the screen.

    """
    waiting = []
    def __uinit__(self, axisnum):
        """
        Construct MouseAxis.
        INPUT ARGS:
          axisnum- mouse axis this object should correspond to
        """
        mechinput.Axis.__init__(self, "Mouse axis %d" % axisnum, 0, mousetrack.screensize[axisnum])
        self.axisnum = axisnum
        track = MouseTrack.lastInstance()
        if track:
            track.assignAxis(self, axisnum)
        else:
            MouseAxis.waiting.append(self)
    def __setstate__(self, state):
        """
        Attach to MouseTrack upon unpickling.
        """
        self.__dict__.update(state)
        track = MouseTrack.lastInstance()
        if track:
            track.assignAxis(self, self.axisnum)
        else:
            MouseAxis.waiting.append(self)
    def __getstate__(self):
        """
        """
        d = self.__dict__.copy()
        try:
            del d["track"]
        except KeyError:
            pass
        return d

class MouseRoller(UniquelyConstructed, mechinput.Roller):
    """
    Roller representing a mouse axis.

    Mouserollers represent a mouse's relative movement.  It differs
    from a MouseAxis because it is NOT limited by the edges of the
    screen.
    """
    waiting = []
    def __uinit__(self, axisnum):
        """
        Construct MouseRoller.
        INPUT ARGS:
          rollernum- mouse roller this object should correspond to
        """
        mechinput.Roller.__init__(self, "Roller for mouse axis %d" % axisnum)
        self.axisnum = axisnum
        track = MouseTrack.lastInstance()
        if track:
            track.assignRoller(self, axisnum)
        else:
            MouseRoller.waiting.append(self)
    def __setstate__(self, state):
        """
        Attach to MouseTrack upon unpickling.
        """
        self.__dict__.update(state)
        track = MouseTrack.lastInstance()
        if track:
            track.assignRoller(self, self.axisnum)
        else:
            MouseRoller.waiting.append(self)
    def __getstate__(self):
        """
        """
        d = self.__dict__.copy()
        try:
            del d["track"]
        except KeyError:
            pass
        return d

class MouseTrack(LogTrack):
    """
    A Track for mouse input.
    """
    trackTypeName = "MouseTrack"
    logExtension = ".mouselog"
    def __init__(self, basename, archive = None, autoStart = True):
        """
        Create the MouseTrack.
        INPUT ARGS:
          basename- filename base for mouse log.
          archive- OPTIONAL directory to put logfile in.
          autoStart- (default is True) If False, does startService and
            startLogging are not called and must be done manually.
            
        """
        LogTrack.__init__(self, basename, archive, autoStart)
        self.buttons = weakref.WeakValueDictionary()
        self.axes = weakref.WeakValueDictionary()
        self.rollers = weakref.WeakValueDictionary()
        for x in MouseButton.waiting:
            self.assignButton(x, x.buttonnum)
        MouseButton.waiting = []
        for x in MouseAxis.waiting:
            self.assignAxis(x, x.axisnum)
        MouseAxis.waiting = []
        for x in MouseRoller.waiting:
            self.assignRoller(x, x.axisnum)
        MouseRoller.waiting = []

    def startService(self):
        """
        Starts the mouse service.
        """
        self.screensize = hardware.getMouseRange()
        self.screensize = (float(self.screensize[0]), float(self.screensize[1]))
        hardware.setMouseCallbacks(self.move_callback, self.button_callback)

    def stopService(self):
        """
        Starts the mouse service.
        """
        hardware.setMouseCallbacks(None, None)
    def button(self, buttonnum):
        """
        Return a Button object mapped to the button specified.
        Identical to calling MouseButton's constructor.
        """
        try:
            return self.buttons[buttonnum]
        except KeyError:
            return MouseButton(buttonnum)
    def assignButton(self, button, buttonnum):
        """
        Internal use only.
        Send all events for indicated mouse button to button object.
        """
        self.buttons[buttonnum] = button
    def getButtons(self):
        """
        Return a 3-tuple of the the mouse buttons.

        OUTPUT ARGS:
          buttons- a 3-tuple of the button objects on this mouse.
        """
        return self.button(1), self.button(2), self.button(3)
    def axis(self, axisnum):
        """
        Return an Axis object mapped to the axis specified.
        This is identical to calling MouseAxis directly!
        """
        try:
            return self.axes[axisnum]
        except KeyError:
            return MouseAxis(axisnum)
    def assignAxis(self, axis, axisnum):
        """
        Internal use only.
        
        Send all events for indicated mouse axis to axis object.
        """
        self.axes[axisnum] = axis
    def getAxes(self):
        """
        Return a 2-tuple of the X and Y axes.

        OUTPUT ARGS:
          axes- a 2-tuple of the two mouse axes objects.
        """
        return self.axis(0), self.axis(1)
    def roller(self, axisnum):
        """
        Return an Roller object mapped to the axis specified.
        Same as calling MouseRoller's constructor directly.
        """
        try:
            return self.rollers[axisnum]
        except KeyError:
            return MouseRoller(axisnum)
    def assignRoller(self, roller, axisnum):
        """
        Internal use only.
        
        Send all events for indicated mouse axis to roller object.
        """
        self.rollers[axisnum] = roller
    def getRollers(self):
        """
        Return a 2-tuple of the X and Y rollers (mapped to the axes).

        OUTPUT ARGS:
          axes- a 2-tuple of the two mouse Roller objects.
        """
        return self.roller(0), self.roller(1)
    def mouseButtonChooser(self):
        """
        Return a ButtonChooser object for all mouse buttons.

        OUTPUT ARGS:
          bc- a ButtonChooser object
        """
        return mechinput.ButtonChooser(*self.getButtons())
    def mouseAxisChooser(self):
        """
        Return an AxisChooser object for both mouse axes.
        OUTPUT ARGS:
         ac- an AxisChooser object
        """
        return mechinput.AxisChooser(*self.getAxes())
    def mouseRollerChooser(self):
        """
        Return a RollerChooser object for both mouse rollers.
        OUTPUT ARGS:
          rc- a RollerChooser object
        
        """
        return mechinput.RollerChooser(*self.getRollers())
    
    setPosition = staticmethod(hardware.setMousePosition)
    setVisibility = staticmethod(hardware.setMouseVisibility)

    def button_callback(self, buttonnum, pressed, timestamp):
        """
        For internal use only.
        This callback is called for every mouse button event.
        """
        if pressed:
            self.logMessage("P\t%d" % buttonnum, timestamp)
        else:
            self.logMessage("R\t%d" % buttonnum, timestamp)
        try:
            self.buttons[buttonnum].setPressed(pressed, timestamp)
        except KeyError:
            pass
    def move_callback(self, pos, rel, timestamp):
        """
        For internal use only.        
        This callback is called for every mouse movement event.
        """
        self.logMessage("M\t%s\t%s" % (pos, rel), timestamp)
        try:
            self.axes[0].setPosition(pos[0], timestamp)
        except KeyError:
            pass
        try:
            self.axes[1].setPosition(pos[1], timestamp)
        except KeyError:
            pass
        try:
            self.rollers[0].move(rel[0])
        except KeyError:
            pass
        try:
            self.rollers[1].move(rel[1])
        except KeyError:
            pass
