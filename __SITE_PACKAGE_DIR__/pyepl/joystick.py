# PyEPL: joystick.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides access to joysticks.
"""

import weakref
from textlog import LogTrack
from base import UniquelyConstructed
import convenience
import hardware
import mechinput
import timing
import sys
import keyboard
from display import VideoTrack

class JoyButton(UniquelyConstructed, mechinput.Button):
    """
    Button representing a joystick button.  Gets its callback
    functionality from the mechinput.Button class.
    """
    waiting = []
    def __uinit__(self, joysticknum, buttonnum):
        """
        Construct JoyButton.
        INPUT ARGS:
          joysticknum- Number of the joystick of interest
          buttonnum- Button number on that joystick.
        OUTPUT ARGS:
          jb- JoyButton object.
        """
        mechinput.Button.__init__(self, "Button %d of Joystick %d" % (buttonnum, joysticknum))
        self.joysticknum = joysticknum
        self.buttonnum = buttonnum
        track = JoyTrack.lastInstance()
        if track:
            track.assignButton(self, joysticknum, buttonnum)
        else:
            JoyButton.waiting.append(self)
    def __setstate__(self, state):
        """
        Attach to JoyTrack upon unpickling.
        """
        self.__dict__.update(state)
        track = JoyTrack.lastInstance()
        if track:
            track.assignButton(self, self.joysticknum, self.buttonnum)
        else:
            JoyButton.waiting.append(self)
    def __getstate__(self):
        """
        """
        d = self.__dict__.copy()
        try:
            del d["track"]
        except KeyError:
            pass
        return d

class JoyAxis(UniquelyConstructed, mechinput.Axis):
    """
    Button representing a joystick axis.
    """
    waiting = []
    def __uinit__(self, joysticknum, axisnum):
        """
        Construct JoyAxis.
        """
        mechinput.Axis.__init__(self, "Axis %d of Joystick %d" % (axisnum, joysticknum))
        self.joysticknum = joysticknum
        self.axisnum = axisnum
        track = JoyTrack.lastInstance()
        if track:
            track.assignAxis(self, joysticknum, axisnum)
        else:
            JoyAxis.waiting.append(self)
    def __setstate__(self, state):
        """
        Attach to JoyTrack upon unpickling.
        """
        self.__dict__.update(state)
        track = JoyTrack.lastInstance()
        if track:
            track.assignAxis(self, self.joysticknum, self.axisnum)
        else:
            JoyAxis.waiting.append(self)
    def __getstate__(self):
        """
        """
        d = self.__dict__.copy()
        try:
            del d["track"]
        except KeyError:
            pass
        return d

class JoyBall(UniquelyConstructed, mechinput.Roller):
    """
    Button representing a joystick ball axis.
    """
    waiting = []
    def __uinit__(self, joysticknum, ballnum, ballaxis):
        """
        Construct JoyBall.
        """
        mechinput.Axis.__init__(self, "Ball %d of Joystick %d, Axis #%d" % (ballnum, joysticknum, ballaxis))
        self.joysticknum = joysticknum
        self.ballnum = ballnum
        self.ballaxis = ballaxis
        track = JoyTrack.lastInstance()
        if track:
            track.assignBall(self, joysticknum, ballnum, ballaxis)
        else:
            JoyBall.waiting.append(self)
    def __setstate__(self, state):
        """
        Attach to JoyTrack upon unpickling.
        """
        self.__dict__.update(state)
        track = JoyTrack.lastInstance()
        if track:
            track.assignBall(self, self.joysticknum, self.ballnum, self.ballaxis)
        else:
            JoyBall.waiting.append(self)
    def __getstate__(self):
        """
        """
        d = self.__dict__.copy()
        try:
            del d["track"]
        except KeyError:
            pass
        return d

class JoyHat(UniquelyConstructed, mechinput.Button):
    """
    Button representing a joystick ball axis.
    """
    waiting = []
    def __uinit__(self, joysticknum, hatnum, hatposx, hatposy):
        """
        Construct JoyHat.
        """
        mechinput.Axis.__init__(self, "Hat %d of Joystick %d in Position %s" % (hatnum, joysticknum, (hatposx, hatposy)))
        self.joysticknum = joysticknum
        self.hatnum = hatnum
        self.hatpos = (hatposx, hatposy)
        track = JoyTrack.lastInstance()
        if track:
            track.assignHat(self, joysticknum, hatnum, hatpos)
        else:
            JoyHat.waiting.append(self)
    def __setstate__(self, state):
        """
        Attach to JoyTrack upon unpickling.
        """
        self.__dict__.update(state)
        track = JoyTrack.lastInstance()
        if track:
            track.assignHat(self, self.joysticknum, self.hatnum, self.hatpos)
        else:
            JoyHat.waiting.append(self)
    def __getstate__(self):
        """
        """
        d = self.__dict__.copy()
        try:
            del d["track"]
        except KeyError:
            pass
        return d

class JoyTrack(LogTrack):
    """
    A Track for joystick input.
    """
    trackTypeName = "JoyTrack"
    logExtension = ".joylog"
    def __init__(self, basename, archive = None, autoStart = True):    
        """
        Create the JoyTrack.
        INPUT ARGS:
          basename- filename base for joystick log.
          archive- OPTIONAL directory to put logfile in.
          autoStart- (default is True) If False, does startService and
            startLogging are not called and must be done manually.
        """
        LogTrack.__init__(self, basename,archive,autoStart)
        self.buttons = weakref.WeakValueDictionary()
        self.axes = weakref.WeakValueDictionary()
        self.balls = weakref.WeakValueDictionary()
        self.hats = weakref.WeakValueDictionary()
        self.hatlast = weakref.WeakValueDictionary()
        for x in JoyButton.waiting:
            self.assignButton(x, x.joysticknum, x.buttonnum)
        JoyButton.waiting = []
        for x in JoyAxis.waiting:
            self.assignAxis(x, x.joysticknum, x.axisnum)
        JoyAxis.waiting = []
        for x in JoyBall.waiting:
            self.assignBall(x, x.joysticknum, x.ballnum, x.ballaxis)
        JoyBall.waiting = []
        for x in JoyHat.waiting:
            self.assignHat(x, x.joysticknum, x.hatnum, x.hatpos)
        JoyHat.waiting = []
    def startService(self):
        """
        Starts the JoyTrack service.
        """
        hardware.setJoystickCallbacks(self.axis_callback, self.ball_callback, self.button_callback, self.hat_callback)
    def stopService(self):
        """
        Stops the JoyTrack service.
        """
        hardware.setJoystickCallbacks(None, None, None, None)
    def calibrate(self):
        """
        Perform interactive joystick calibration if needed.
        """
        if sys.platform == "darwin":
            self.logMessage("CALIBRATE_START\tCalibration begins")
            VideoTrack.lastInstance().clear("black")
            convenience.instruct(
            """
            Please calibrate the JOYSTICK(S) now...

            Move the JOYSTICK(S) all the way UP.

            Move the JOYSTICK(S) all the way DOWN.

            Move the JOYSTICK(S) all the way LEFT.

            Move the JOYSTICK(S) all the way RIGHT.

            Press the 0 button on JOYSTICK 0 when finished.

            If no JOYSTICK, press SPACE.
            """,
            exitbutton = self.button(0, 0) | keyboard.Key("SPACE"),
            size = 0.04
            )
            self.logMessage("CALIBRATE_END\tCalibration ends")
    def button(self, joysticknum, buttonnum):
        """
        Returns a Button object mapped to the button specified.
        This is identical to calling the JoyButton constructor directly.
        """
        return JoyButton(joysticknum, buttonnum)
    def assignButton(self, button, joysticknum, buttonnum):
        """
        For internal use only.
        
        Send all events for indicated joystick button to button
        object.
        """
        if self.buttons.has_key((joysticknum, buttonnum)):
            raise ValueError, "Button %d of joystick %d already bound" % (buttonnum, joysticknum)
        self.buttons[(joysticknum, buttonnum)] = button
    def axis(self, joysticknum, axisnum):
        """
        Return an Axis object mapped to the joystick axis specified.
        This is identical to calling the JoyAxis constructor directly.
        """
        return JoyAxis(joysticknum, axisnum)
    def assignAxis(self, axis, joysticknum, axisnum):
        """
        For internal use only.
        
        Send all events for indicated joystick axis to axis object.
        """
        if self.axes.has_key((joysticknum, axisnum)):
            raise ValueError, "Axis %d of joystick %d already bound" % (axisnum, joysticknum)
        self.axes[(joysticknum, axisnum)] = axis
    def ball(self, joysticknum, ballnum, ballaxis):
        """
        Return a Roller object mapped to the joystick ball specified.
        This is identical to calling the JoyBall constructor directly.
        """
        return JoyBall(joysticknum, ballnum, ballaxis)
    def assignBall(self, ball, joysticknum, ballnum, ballaxis):
        """
        For internal use only.
        
        Send all events for indicated joystick ball axis to roller
        object.
        """
        if self.axes.has_key((joysticknum, axisnum, ballaxis)):
            raise ValueError, "Axis %d of ball %d of joystick %d already bound" % (ballaxis, ballnum, joysticknum)
        self.balls[(joysticknum, ballnum, ballaxis)] = ball
    def hat(self, joysticknum, hatnum, hatpos):
        """
        Return a Button object mapped to the joystick hat and hat
        position specified.

        This is identical to calling the JoyHat constructor directly.
        """
        return JoyHat(joysticknum, hatnum, hatpos)
    def assignHat(self, hat, joysticknum, hatnum, hatpos):
        """
        For internal use only.
        
        Send all events for indicated joystick hat position to roller
        object.
        """
        if self.axes.has_key((joysticknum, hatnum, hatpos)):
            raise ValueError, "Position %r of hat %d of joystick %d already bound" % (hatpos, hatnum, joysticknum)
        self.balls[(joysticknum, ballnum, ballaxis)] = ball
        self.hats[(joysticknum, hatnum, hatpos)] = hat
    def joyButtonChooser(self):
        """
        Return a ButtonChooser object for all joystick hats and buttons.

        OUTPUT ARGS:
          buttonChooser- a mechinput.ButtonChoser object.
        """
        allbuttons = []
        features = hardware.getJoystickFeatures()
        for jn, js in enumerate(features):
            for hn in xrange(js[3]):
                allbuttons.append(self.hat(jn, hn, (1, 0)))
                allbuttons.append(self.hat(jn, hn, (-1, 0)))
                allbuttons.append(self.hat(jn, hn, (1, 1)))
                allbuttons.append(self.hat(jn, hn, (1, -1)))
                allbuttons.append(self.hat(jn, hn, (0, 1)))
                allbuttons.append(self.hat(jn, hn, (0, -1)))
                allbuttons.append(self.hat(jn, hn, (-1, -1)))
                allbuttons.append(self.hat(jn, hn, (-1, 1)))
                # hats at position (0, 0) are excluded from the returned button chooser
            for bn in xrange(js[2]):
                allbuttons.append(self.button(jn, bn))
        return mechinput.ButtonChooser(*allbuttons)
    def joyAxisChooser(self):
        """
        Return an AxisChooser object for all joystick axes.

        OUTPUT ARGS:
          axisChooser- a mechinput.ButtonChoser object.
        """
        allaxes = []
        features = hardware.getJoystickFeatures()
        for jn, js in enumerate(features):
            for an in xrange(js[0]):
                allaxes.append(self.axis(jn, an))
        return mechinput.AxisChooser(*allaxes)
    def joyBallChooser(self):
        """
        Return a RollerChooser object for all joystick balls.
        OUTPUT ARGS:
          joyBallChooser- a mechinput.ButtonChoser object.
        """
        allballs = []
        features = hardware.getJoystickFeatures()
        for jn, js in enumerate(features):
            for bn in xrange(js[2]):
                allballs.append(self.ball(jn, bn, 0))
                allballs.append(self.ball(jn, bn, 1))
        return mechinput.RollerChooser(*allballs)
    def button_callback(self, joysticknum, buttonnum, pressed, timestamp):
        """
        For internal use only.
        
        This callback is called for every joystick button event.
        """
        if self.logall:
            if pressed:
                self.logMessage("P\t%d\t%d" % (joysticknum, buttonnum), timestamp)
            else:
                self.logMessage("R\t%d\t%d" % (joysticknum, buttonnum), timestamp)
        try:
            self.buttons[(joysticknum, buttonnum)].setPressed(pressed, timestamp)
        except KeyError:
            pass
    def axis_callback(self, joysticknum, axisnum, position, timestamp):
        """
        For internal use only.
        
        This callback is called for every joystick axis event.
        """
        if self.logall:
            self.logMessage("A\t%d\t%d\t%f" % (joysticknum, axisnum, position), timestamp)
        try:
            self.axes[(joysticknum, axisnum)].setPosition(position, timestamp)
        except KeyError:
            pass
    def ball_callback(self, joysticknum, ballnum, relpos, timestamp):
        """
        For internal use only.
        
        This callback is called for every joystick ball event.
        """
        if self.logall:
            self.logMessage("L\t%d\t%d\t%f" % (joysticknum, ballnum, relpos), timestamp)
        try:
            self.balls[(joysticknum, ballnum, 0)].move(relpos[0])
        except KeyError:
            pass
        try:
            self.balls[(joysticknum, ballnum, 1)].move(relpos[1])
        except KeyError:
            pass
    def hat_callback(self, joysticknum, hatnum, position, timestamp):
        """
        For internal use only.
        
        This callback is called for every joystick hat event.
        """
        if self.logall:
            self.logMessage("H\t%d\t%d\t%s" % (joysticknum, hatnum, position), timestamp)
        try:
            self.hatlast[(joysticknum, hatnum)].setPressed(False, timestamp)
        except KeyError:
            pass
        try:
            self.hatlast[(joystick, hatnum)] = self.hats[(joysticknum, hatnum, position)]
        except KeyError:
            pass
        try:
            self.hats[(joysticknum, hatnum, position)].setPressed(True, timestamp)
        except KeyError:
            pass
