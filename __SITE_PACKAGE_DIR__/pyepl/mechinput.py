# PyEPL: mechinput.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides a layer of abstraction to the input data of
mechanical input devices (i.e. mouse, keyboard, joystick).
"""

from repository import WeakKeyDictionary, MethodCallback
import sys
import timing
import hardware

class Roller:
    """
    Abstraction to any continuous motion component without bounds.
    """
    def __init__(self, name = None):
        """
        Set up housekeeping.
        """
        if name == None:
            self.name = repr(self)
        else:
            self.name = name
        self.callbacks = WeakKeyDictionary() # callback -> args
        self.counter = 0.0
        self.parents = ()
    def __mul__(self, x):
        """
        Return a ScaledRoller.
        """
        return ScaledRoller(self, x)
    __rmul__ = __mul__
    def move(self, amount):
        """
        Add to cumulative change in position.

        INPUT ARGS:
          amount- The amount to move (arbitrary units).
        """
        if amount:
            self.counter = self.counter + amount
            for c, args in self.callbacks.items():
                c(amount, *args)
    def update(self):  # to be overridden
        """
        Keep the value up to date.
        """
        for parent in self.parents:
            parent.update()
    def getChange(self):
        """
        Get cumulative change since last getChange (or since
        initialization).
        """
        self.update()
        c = self.counter
        self.counter = 0.0
        return c
    def addCallback(self, c, *args):
        """
        Call c(change, *args) whenever the position changes.  This
        Roller's reference to c will be weak.
        """
        self.callbacks[c] = args
    def echo(self):
        """
        Return an EchoRoller of this Roller.
        """
        return EchoRoller(self)
Roller.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class EchoRoller(Roller):
    """
    """
    def __init__(self, roller):
        """
        """
        Roller.__init__(self, "EchoRoller for %s" % roller.name)
        self.roller = roller
        self.parents = (roller,)
        self.cb = MethodCallback(self.move)
        roller.addCallback(self.cb)
    def echo(self):
        """
        Return an EchoRoller of this Roller.
        """
        return EchoRoller(self.roller)
EchoRoller.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class ThrottledRoller(Roller):
    """
    Roller based on another Roller, but throttled by a maximum
    velocity and/or a maximum acceleration.
    """
    def __init__(self, roller, maxAccel = None, maxVel = None, name = None):
        """
        Create a ThrottledRoller with maxAccel roller units per
        millisecond per millisecond maximum acceleration and maxVel
        roller units per millisecond maximum velocity.  None for
        either of those values means that the constraint will not be
        applied.
        """
        if name == None:
            name = "ThrottledRoller from %s" % roller.name
        else:
            name = name
        Roller.__init__(self, name)
        self.roller = roller
        self.parents = [roller]
        self.maxAccel = maxAccel
        self.maxVel = maxVel
        self.accum = 0.0
        self.lastvelocity = 0.0
        self.lasttime = timing.now()
        self.cb = MethodCallback(self.callback)
        roller.addCallback(self.cb)
    def update(self):
        """
        Keep the value up to date.
        """
        Roller.update(self)
        self.callback(0.0)
    def callback(self, change):
        """
        Callback used to communicate with parent Roller.  The parent
        roller passes the amount that it is changeing to the callback.
        """
        thistime = timing.now()
        elapsed = thistime - self.lasttime
        if not elapsed:
            self.accum = self.accum + change
            return
        change = change + self.accum
        self.accum = 0.0
        thisvelocity = change / elapsed
        if self.maxAccel:
            if abs(thisvelocity - self.lastvelocity) / elapsed > self.maxAccel:
                if thisvelocity < self.lastvelocity:
                    thisvelocity = self.lastvelocity - self.maxAccel * elapsed
                else:
                    thisvelocity = self.lastvelocity + self.maxAccel * elapsed
        if self.maxVel:
                if thisvelocity > self.maxVel:
                    thisvelocity = self.maxVel
                elif thisvelocity < -self.maxVel:
                    thisvelocity = -self.maxVel
        self.lasttime = thistime
        self.lastvelocity = thisvelocity
        self.move(thisvelocity * elapsed)
ThrottledRoller.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class ScaledRoller(Roller):
    """
    Roller based on another roller such that all positive motion is
    proportional to all positive motion in the parent and all negative
    motion is proportional to all motion of the parent.
    """
    def __init__(self, roller, scale, reverse_scale = None, name = None):
        """
        Create ScaledRoller with 'scale' and optionally different
        'reverse_scale'.
        """
        if name == None:
            name = "ScaledRoller from %s" % roller.name
        else:
            name = name
        Roller.__init__(self, name)
        if reverse_scale == None:
            self.reverse_scale = scale
        else:
            self.reverse_scale = reverse_scale
        self.forward_scale = scale
        self.roller = roller
        self.parents = [roller]
        self.cb = MethodCallback(self.callback)
        roller.addCallback(self.cb)
    def callback(self, change):
        """
        Callback used to communicate with parent Roller.
        """
        if change < 0:
            self.move(change * self.reverse_scale)
        else:
            self.move(change * self.forward_scale)
ScaledRoller.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class JointRoller(Roller):
    """
    Roller whose motion equals the sum of the motions of certain other
    Rollers.
    """
    def __init__(self, *rollers):
        """
        Create JointRoller based on rollers.
        """
        Roller.__init__(self, "JointRoller")
        self.rollers = rollers
        self.parents = rollers
        self.cb = MethodCallback(self.move)
        for roller in rollers:
            roller.addCallback(self.cb)
JointRoller.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class Axis:
    """
    Abstraction to any continuous motion component with bounds.
    """
    def __init__(self, name = None, posmin = -1.0, posmax = 1.0):
        """
        Set up housekeeping.
        """
        if name == None:
            self.name = repr(self)
        else:
            self.name = name
        self.callbacks = WeakKeyDictionary() # callback -> args
        self.position = 0.0
        self.posmin = posmin
        self.posmax = posmax
        self.parents = ()
    def halt(self):  # To be overridden
        pass
    def setPosition(self, p, timestamp = None):
        """
        Set the position of this axis between 1.0 and -1.0.
        """
        if p != self.position:
            if timestamp == None:
                timestamp = (timing.now(), long(0))
            self.position = p
            for c, args in self.callbacks.items():
                c(p, timestamp, *args)
    def update(self):  # to be overridden
        """
        Keep the value up to date.
        """
        for parent in self.parents:
            parent.update()
    def getPosition(self):
        """
        Return position.
        """
        self.update()
        return self.position
    def normalize(self, pos):
        """
        Return pos normalized between -1.0 and 1.0.
        """
        return 2 * (pos - self.posmin) / (self.posmax - self.posmin) - 1
    def getNormalized(self):
        """
        Return position normalized between -1.0 and 1.0.
        """
        self.update()
        return self.normalize(self.position)
    def addCallback(self, c, *args):
        """
        Call c(position, timestamp, *args) whenever the position
        changes.  This axis' reference to c will be weak.
        """
        self.callbacks[c] = args
    def __mul__(self, other):
        """
        """
        return ScaledAxis(self, other)
Axis.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class ScaledAxis(Axis):
    """
    A virtual Axis whose position is always equal to the position of a
    source Axis times a constant.
    """
    def __init__(self, axis, scale, rscale = None, name = None):
        """
        Create ScaledAxis based on axis with specified scale.
        """
        if name == None:
            name = "ScaledAxis (%s * %f)" % (axis.name, scale)
        else:
            name = name
        if rscale is None:
            rscale = scale
        Axis.__init__(self, name, axis.posmin * scale, axis.posmax * scale)
        self.axis = axis
        self.scale = scale
        self.rscale = rscale
        self.cb = MethodCallback(self.callback)
        axis.addCallback(self.cb)
        self.parents = (axis,)
    def callback(self, position, timestamp):
        """
        This method accepts information from the source axis.
        """
        if position > 0:
            self.setPosition(position * self.scale, timestamp)
        else:
            self.setPosition(position * self.rscale, timestamp)
ScaledAxis.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class AxisScaledAxis(Axis):
    """
    """
    def __init__(self, axis1, axis2, name = None):
        """
        """
        if name == None:
            name = "AxisScaledAxis (%s * %s)" % (axis1, axis2)
        else:
            name = name
        Axis.__init__(self, name, axis1.posmin * axis2.posmin, axis1.posmax * axis2.posmax)
        self.axis1 = axis1
        self.axis2 = axis2
        self.cb = MethodCallback(self.callback)
        axis1.addCallback(self.cb)
        axis2.addCallback(self.cb)
        self.parents = (axis1, axis2)
    def callback(self, position, timestamp):
        """
        """
        self.setPosition(self.axis1.getPosition() * self.axis2.getPosition())
AxisScaledAxis.__module__ = "pyepl.mechinput"  # cope with pyrex bug

def getPosMin(x):
    return x.posmin

def getPosMax(x):
    return x.posmax

class JointAxis(Axis):
    """
    A virtual Axis whose position is always equal to the sum of its
    source axes.  Its normalized position is always equal to the mean
    of the normalized positions of it source axes.
    """
    def __init__(self, *axes):
        """
        Arguments are taken as source axes.
        """
        Axis.__init__(self, "JointAxis", min(map(getPosMin, axes)), max(map(getPosMax, axes)))
        self.axes = axes
        self.cb = MethodCallback(self.callback)
        self.positions = []
        for n, axis in enumerate(axes):
            axis.addCallback(self.cb, n)
            self.positions.append(0.0)
        self.parents = axes
        self.sum = 0.0
    def callback(self, position, timestamp, n):
        """
        Callback used for communication with source axes.
        """
        self.sum = self.sum + (position - self.positions[n])
        self.positions[n] = position
        self.setPosition(self.sum, timestamp)
JointAxis.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class ThrottledAxis(Axis):
    """
    """
    def __init__(self, axis, maxVel = None, maxAccel = None, name = None):
        """
        """
        if name == None:
            name = "ThrottledAxis from %s" % axis.name
        else:
            name = name
        Axis.__init__(self, name, axis.posmin, axis.posmax)
        self.axis = axis
        self.lasttime = timing.now()
        self.lastpos = axis.getPosition()
        self.lastspeed = 0.0
        self.maxVel = maxVel
        self.maxAccel = maxAccel
        self.cb = MethodCallback(self.callback)
        axis.addCallback(self.cb)
        self.parents = (axis,)
    def halt(self):
        """
        """
        self.lastspeed = 0.0
        self.lastpos = 0.0
    def update(self):
        """
        """
        self.callback(self.axis.getPosition(), (timing.now(), long(0)))
    def callback(self, position, timestamp):
        """
        """
        thistime = timestamp[0]
        interval = thistime - self.lasttime
        if not interval:
            return
        speed = (position - self.lastpos) / interval
        accel = (speed - self.lastspeed) / interval
        if not self.maxAccel is None:
            if accel > self.maxAccel:
                speed = self.lastspeed + (self.maxAccel * interval)
            elif accel < -self.maxAccel:
                speed = self.lastspeed - (self.maxAccel * interval)
        if not self.maxVel is None:
            if speed > self.maxVel:
                speed = self.maxVel
            elif speed < -self.maxVel:
                speed = -self.maxVel
        position = self.lastpos + (speed * interval)
        self.setPosition(position, timestamp)
        self.lasttime = thistime
        self.lastpos = position
        self.lastspeed = speed
ThrottledAxis.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class RollerAxis(Axis):
    """
    A virtual Axis whose position is controlled by the movement of a
    Roller.
    """
    def __init__(self, roller, min = -1.0, max = 1.0, start = 0.0, name = None):
        """
        Create RollerAxis from roller.  min, max, and start may be
        used to specify minimum position, maximum position, and
        starting position, respectively.
        """
        if name == None:
            name = "RollerAxis from %s" % roller.name
        else:
            name = name
        Axis.__init__(self, name, min, max)
        self.roller = roller
        self.min = min
        self.max = max
        self.setPosition(start)
        self.cb = MethodCallback(self.callback)
        roller.addCallback(self.cb)
    def callback(self, delta):
        """
        Callback for communicating with the attached roller.
        """
        newpos = self.getPosition() + delta
        if newpos > max:
            newpos = max
        elif newpos < min:
            newpos = min
        self.setPosition(newpos)
    def getPosition(self):
        """
        Update roller first!
        """
        self.roller.update()
        return Axis.getPosition(self)
RollerAxis.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class AxisRoller(Roller):
    """
    Roller whose rate of change is controlled by the position of an
    axis.
    """
    def __init__(self, axis, speedfactor = 1.0, backwardspeedfactor = None, name = None):
        """
        Create AxisRoller from axis with specified speedfactor
        (defaults to 1.0).  Speedfactor units are roller units per
        millisecond per axis unit.
        """
        if name == None:
            name = "AxisRoller from %s" % axis.name
        else:
            name = name
        if backwardspeedfactor is None:
            backwardspeedfactor = speedfactor
        Roller.__init__(self, name)
        self.axis = axis
        self.speedfactor = speedfactor
        self.backwardspeedfactor = backwardspeedfactor
        self.lasttime = timing.now()
    def update(self):
        """
        Update the change for this roller in a time-consistent manner.
        """
        Roller.update(self)
        thistime = timing.now()
        elapsed = thistime - self.lasttime
        if elapsed:
            norm = self.axis.getNormalized()
            if norm > 0:
                self.move(elapsed * self.speedfactor * norm)
            else:
                self.move(elapsed * self.backwardspeedfactor * norm)
            self.lasttime = thistime
AxisRoller.__module__ = "pyepl.mechinput"  # cope with pyrex bug

def derivativeAxis(axis, speedfactor = 1.0, min = -1.0, max = 1.0, start = 0.0, name = None):
    """
    Get an axis whose position's rate of change is proportional to the
    position of the input axis within min and max absolute position
    boundaries.
    """
    if name == None:
        name = "Axis derived from %s" % axis.name
    else:
        name = name
    return RollerAxis(AxisRoller(axis, speedfactor), min, max, start, name)

class AxisScaledRoller(Roller):
    """
    Movement of parent roller scaled by the normalized position of the
    parent axis and a constant (factor).
    """
    def __init__(self, roller, axis, factor = 1.0, name = None):
        """
        Create AxisScaledRoller.
        """
        if name == None:
            name = "AxisScaledRoller (%s * %s * %f)" % (roller.name, axis.name, factor)
        else:
            name = name
        Roller.__init__(self, name)
        self.roller = roller
        self.parents = [roller]
        self.axis = axis
        self.factor = factor
        self.cb = MethodCallback(self.callback)
        roller.addCallback(self.cb)
    def callback(self, delta):
        """
        Callback for communicating with the attached roller.
        """
        self.move(delta * self.axis.getNormalized() * self.factor)
AxisScaledRoller.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class Button:
    """
    Abstraction to any on/off input component.
    """
    def __init__(self, name = None):
        """
        Set up housekeeping.
        """
        if name == None:
            self.name = repr(self)
        else:
            self.name = name
        self.callbacks = WeakKeyDictionary() # callback -> args
        self.pressed = False
        self.presstime = None
    def __getstate__(self):
        """
        Don't give pickle hardware states.
        """
        return self.name, self.callbacks
#        return self.name
    def __setstate__(self, state):
        """
        Reset hardware states when unpickled.
        """
        self.name, self.callbacks = state
#        self.name = state
        self.pressed = False
        self.presstime = None
    def __and__(self, x):
        """
        And operator creates a ButtonCombo.
        """
        return ButtonCombo(self, x)
    def __or__(self, x):
        """
        Or operator creates an EitherCombo.
        """
        return EitherButton(self, x)
    def setPressed(self, p, timestamp = None):
        """
        Set the pressed state of this button (True or False).
        """
        if p != self.pressed:
            if timestamp == None:
                timestamp = (timing.now(), long(0))
            self.presstime = timestamp
            self.pressed = p
            for c, args in self.callbacks.items():
                c(p, timestamp, *args)
    def isPressed(self):
        """
        Return True if pressed.  Otherwise return False.
        """
        return self.pressed
    def wait(self, clk = None, pressed = True):
        """
        Wait until this button's pressed state matches the argument
        pressed.  Returns the time at which the state matched.  If clk
        is supplied (a PresentationClock), it will be updated to the
        time at which the state became matching.
        """
        while pressed != self.pressed:
            hardware.pollEvents()
        if clk:
            clk.tare(self.presstime)
        return self.presstime
    def addCallback(self, c, *args):
        """
        Call c(pressed, timestamp, *args) whenever the state changes.
        This button's reference to c will be weak.
        """
        self.callbacks[c] = args
Button.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class ButtonCombo(Button):
    """
    Vitrual button that is considered pressed when a combination of
    other buttons is pressed.
    """
    def __init__(self, *combo):
        """
        Create ButtonCombo.  Arguments of buttons to be included in
        the combination.
        """
        Button.__init__(self, "Button combination (AND)")
        self.state = []
        self.combo = combo
        self.cb = MethodCallback(self.callback)
        for n, button in enumerate(combo):
            button.addCallback(self.cb, n)
            self.state.append(button.isPressed())
    def callback(self, pressed, timestamp, n):
        """
        Callback used for communication with the buttons which are a
        part if this combination.
        """
        self.state[n] = pressed
        if False in self.state:
            self.setPressed(False, timestamp)
        else:
            self.setPressed(True, timestamp)
ButtonCombo.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class EitherButton(Button):
    """
    Virtual button this is considered pressed when any one of a set of
    other buttons is pressed.
    """
    def __init__(self, *set):
        """
        Create EitherButton.  Arguments of buttons to be included in
        the set.
        """
        Button.__init__(self, "Button set (OR)")
        self.state = []
        self.set = set
        self.cb = MethodCallback(self.callback)
        for n, button in enumerate(set):
            button.addCallback(self.cb, n)
            self.state.append(button.isPressed())
    def callback(self, pressed, timestamp, n):
        """
        Callback used for communication with the buttons which are a
        part if this set.
        """
        self.state[n] = pressed
        if True in self.state:
            self.setPressed(True, timestamp)
        else:
            self.setPressed(False, timestamp)
EitherButton.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class NotchRoller(Roller):
    """
    Roller whose position is changed in discreet amounts upon the
    depression of certain buttons.
    """
    def __init__(self, *buttonamounts):
        """
        Constructor takes any number of 2-tuples: (Button, amount).
        """
        Roller.__init__(self, "NotchRoller")
        self.buttonamounts = buttonamounts
        self.cb = MethodCallback(self.callback)
        for buttonamount in buttonamounts:
            buttonamount[0].addCallback(self.cb, buttonamount[1])
    def callback(self, pressed, timestamp, amount):
        """
        Callback used for communication with the Buttons.
        """
        if pressed:
            self.move(amount)
NotchRoller.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class ButtonRoller(Roller):
    """
    Roller whose rate of change is controlled by two buttons.
    """
    def __init__(self, inc_button, dec_button, speed = 1.0, backspeed = None, name = None):
        """
        Create ButtonRoller where inc_button being pressed causes
        positive movement at speed roller units per millisecond and
        dec_button being pressed causes negative movement at speed
        roller units per millisecond.
        """
        if name is None:
            name = "ButtonRoller from %s and %s" % (inc_button.name, dec_button.name)
        else:
            name = name
        if backspeed is None:
            backspeed = speed
        Roller.__init__(self, name)
        self.inc_button = inc_button
        self.dec_button = dec_button
        self.speed = speed
        self.backspeed = backspeed
        self.lasttime = timing.now()
    def update(self):
        """
        Update the Roller's movement in a time-consistent manner.
        """
        Roller.update(self)
        thistime = timing.now()
        elapsed = thistime - self.lasttime
        if elapsed:
            if(self.inc_button.isPressed()):
                self.move(elapsed * self.speed)
            if(self.dec_button.isPressed()):
                self.move(elapsed * -self.backspeed)
            self.lasttime = thistime
ButtonRoller.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class ButtonAxis(Axis):
    """
    Axis whose position is controlled by two buttons.
    """
    def __init__(self, high_button, low_button, magnitude = 1.0, lmagnitude = None, name = None, minpos = -1.0, maxpos = 1.0):
        """
        Create ButtonAxis where pressing high_button sets the axis
        position to magnitude.  Pressing low_button sets the position
        to negative magnitude.  Both or neither button sets the
        position to 0.0.
        """
        if name == None:
            name = "ButtonAxis from %s and %s" % (high_button.name, low_button.name)
        else:
            name = name
        if lmagnitude is None:
            lmagnitude = magnitude
        Axis.__init__(self, name, minpos, maxpos)
        self.high_button = high_button
        self.low_button = low_button
        self.magnitude = magnitude
        self.lmagnitude = lmagnitude
        self.cb = MethodCallback(self.callback)
        high_button.addCallback(self.cb)
        low_button.addCallback(self.cb)
    def callback(self, pressed, timestamp):
        """
        Callback to communicate with buttons.
        """
        if self.high_button.isPressed():
            value = self.magnitude
        else:
            value = 0
        if self.low_button.isPressed():
            value = value - self.lmagnitude
        self.setPosition(value, timestamp)
ButtonAxis.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class AxisButton(Button):
    """
    Button which is considered pressed when a certain axis' position
    falls within a certain range and not otherwise.
    """
    def __init__(self, axis, low = 0.9, high = 1.0, name = None):
        """
        Create AxisButton from axis such that this Button is
        considered pressed when the position of axis falls between low
        and high.
        """
        if name == None:
            name = "AxisButton from %s" % (axis.name)
        else:
            name = name
        Button.__init__(self, name)
        self.axis = axis
        self.low = low
        self.high = high
        self.cb = MethodCallback(self.callback)
        axis.addCallback(self.cb)
    def callback(self, position, timestamp):
        """
        Callback used to communicate with the axis.
        """
        if self.low <= self.axis.normalize(position) <= self.high:
            self.setPressed(True, timestamp)
        else:
            self.setPressed(False, timestamp)
AxisButton.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class ChooserIter:
    def __init__(self, chooser):
        self.chooser = chooser
        self.iterators = [iter(self.chooser.items)]
    def next(self):
        while True:
            try:
                r = self.iterators[-1].next()
            except StopIteration:
                self.iterators.pop()
                continue
            except IndexError:
                raise StopIteration
            if isinstance(r, self.chooser.__class__):
                self.iterators.append(iter(r))
                continue
            break
        return r
ChooserIter.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class Chooser:
    """
    Super-class for input component choosers.
    """
    def __init__(self, *items):
        """
        Initialize.
        """
        self.items = items
        self.chosen = None
        self.timestamp = None
    def __and__(self, x):
        """
        And operator produces a Chooser including the mechanical input
        abstraction objects from both operands.
        """
        return self.__class__(self, x)
    def __iter__(self):
        """
        Get all items in this Chooser, including items within child
        Choosers.
        """
        return ChooserIter(self)
    def choose(self, chosen, timestamp):
        """
        Indicate that an item has been chosen.
        """
        self.chosen = chosen
        self.timestamp = timestamp
    def waitChoice(self, minDuration=None, maxDuration=None, clock=None):
        """
        Wait for an item to be chosen.
        """
        if clock:
            startTime = clock.get()
        else:
            startTime = hardware.universal_time()

        # set up minDuration            
        if minDuration:
            # will wait for minDuration before accepting key presses
            minStart = minDuration + startTime
        else:
            minStart = startTime

        # see if set up maxTime
        if maxDuration:
            stopTime = startTime + maxDuration
        else:
            stopTime = 0
            
        # wait for a keypress that occured after start of wait
        while (self.chosen is None) or (self.timestamp[0] < minStart):
            if maxDuration and stopTime <= hardware.universal_time():
                # we had a max duration, so break
                break
            hardware.pollEvents()

        chosen = self.chosen
        timestamp = self.timestamp

        # if nothing chosen or we are not in the correct range 
        if timestamp is None or timestamp[0]<minStart:
            # set chosen to None
            chosen = None
            #set timestamp to stoptime
            timestamp = (stopTime,0)
        
            
	# if there is a clock, tare the time
	if clock:
	    clock.tare(timestamp)

        # reset the internal chosen button and time
        self.chosen = None
        self.timestamp = None

        # return chosen button and time
        return chosen, timestamp
Chooser.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class ButtonChooser(Chooser):
    """
    This class represents a set of buttons.  It can be used to
    determine which button, out of the set, has been pressed.
    """
    def __init__(self, *buttons):
        """
        Constructs ButtonChooser from a list of possible Buttons and
        other ButtonChoosers.
        """
        Chooser.__init__(self, *buttons)
        self.cb = MethodCallback(self.callback)
        for n, b in enumerate(self):
            b.addCallback(self.cb, n, b)
    def waitWithTime(self, minDuration=None, maxDuration=None, clock=None):
        """
        Wait until a button is _newly_ pressed.  Return a 2-tuple of
        the Button and the time at which it was pressed.
        """
        return self.waitChoice(minDuration,maxDuration,clock)
    def wait(self, minDuration=None, maxDuration=None, clock=None):
        """
        Like wait_with_time, but returns only the Button object.
        """
        return self.waitWithTime(minDuration,maxDuration,clock)[0]
    def callback(self, pressed, timestamp, n, b):
        """
        Callback used to get information from buttons.
        """
        if pressed:
            self.choose(b, timestamp)
ButtonChooser.__module__ = "pyepl.mechinput"  # cope with pyrex bug


class FirstButtonChooser(Chooser):
    """
    This class represents a set of buttons.  It can be used to
    determine which button, out of the set, has been pressed first,
    but only after you have set the minimum start time (and optional
    end time) via the setTimeRange method.

    The primary use of this class is to set some buttons to watch
    during the presentation of some stimuli.  Then you can easily
    determine which button, if any was pressed first during the
    specified time range.
    """

    def __init__(self, *buttons):
        """
        Constructs FirstButtonChooser from a list of possible Buttons and
        other ButtonChoosers.
        """
        Chooser.__init__(self, *buttons)
	self.minTime = None
	self.maxTime = None
        self.cb = MethodCallback(self.callback)
        for n, b in enumerate(self):
            b.addCallback(self.cb, n, b)
    def setTimeRange(self,minTime,maxTime=None):
	"""
	Set the time range within which a button can be chosen.  

	If maxTime is None, then a button can be chosen anytime
	after the minTime.
	"""
	self.chosen = None
	self.timestamp = None
	self.minTime = minTime
	self.maxTime = maxTime
    def callback(self, pressed, timestamp, n, b):
        """
        Callback used to get information from buttons.
        """
	# only press if nothing pressed yet and beyond 
	# earliest start time.
        if pressed and \
		self.chosen is None and \
		not self.minTime is None and \
		timestamp[0] >= self.minTime and \
		(self.maxTime is None or timestamp[0] < self.maxTime):
            self.choose(b, timestamp)
FirstButtonChooser.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class AxisChooser(Chooser):
    """
    This class represents a set of axes.  It can be used to determine
    which axis, out of the set, has been moved to indicate deliberate
    selection.
    """
    def __init__(self, *axes):
        """
        Constructs AxisChooser from a list of possible Axes and other
        AxisChoosers.
        """
        Chooser.__init__(self, *axes)
        self.extrema = []
        self.cb = MethodCallback(self.callback)
        for n, a in enumerate(self):
            a.addCallback(self.cb, n, a)
            self.extrema.append([0, 0])
    def wait(self):
        """
        Wait until an axis has been moved to within ten percent of
        both unit extremes.  Return the axis that first meets this
        criterion.
        """
        self.reset()
        return self.waitChange()[0]
    def reset(self):
        """
        Forget any movement accumulated so far.
        """
        for n in xrange(len(self.extrema)):
            self.extrema[n] = [0, 0]
    def callback(self, position, timestamp, n, a):
        """
        Callback used to get information from axes.
        """
        nposition = a.normalize(position)
        if nposition < self.extrema[n][0]:
            self.extrema[n][0] = nposition
        elif nposition > self.extrema[n][1]:
            self.extrema[n][1] = nposition
        if self.extrema[n][0] < -0.9 and self.extrema[n][1] > 0.9:
            self.choose(a, timestamp)
AxisChooser.__module__ = "pyepl.mechinput"  # cope with pyrex bug

class RollerChooser(Chooser):
    """
    This class represents a set of rollers.  It can be used to
    determine which roller, out of the set, has been moved to indicate
    deliberate selection.
    """
    def __init__(self, *rollers):
        """
        Constructs RollerChooser from a list of possible Rollers and other
        RollerChoosers.
        """
        Chooser.__init__(self, *rollers)
        self.totals = []
        self.cb = MethodCallback(self.callback)
        for n, r in enumerate(self):
            r.addCallback(self.cb, n, r)
            self.totals.append(0.0)
    def wait(self):
        """
        Wait until a roller has been moved five times as much as any
        other roller in the set and at least ten units.  Return that
        roller.
        """
        self.reset()
        return self.waitChoice()[0]
    def reset(self):
        """
        Forget any movement accumulated so far.
        """
        for n in xrange(len(self.totals)):
            self.totals[n] = 0.0
    def callback(self, amount, n, r):
        """
        Callback used to get information from rollers.
        """
        self.totals[n] = self.totals[n] + amount
        for x in self.totals:
            if self.totals[n] > 10 and (self.totals[n] < (x * 5)):
                return
        self.choose(r, None)
RollerChooser.__module__ = "pyepl.mechinput"  # cope with pyrex bug
