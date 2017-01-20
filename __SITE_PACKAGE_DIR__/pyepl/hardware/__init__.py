# PyEPL: hardware/__init__.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This package provides an interface to all the hardware and platform
specific functionality that pyEPL needs.  The interface should always
work the same regardless of the underlying implementation.
"""

import eventpoll
import keyboard
import graphics
import mouse
import joystick
import timing
import vr
import rt
import eeg
import sound

import pygame
import sys

modules = [timing, keyboard, mouse, joystick, graphics, eventpoll, vr, eeg, sound]

def initialize(**options):
    global modules
    pygame.init()
    pygame.mixer.quit()
    for m in modules:
        m.initialize(**options)

def finalize():
    global modules
    rmodules = modules[:]
    rmodules.reverse()
    for m in rmodules:
        m.finalize()
    pygame.quit()

# Timing Features
universal_time = timing.universal_time
timedCall = timing.timedCall
pollEvents = eventpoll.pollEvents
addPollCallback = eventpoll.addPollCallback
removePollCallback = eventpoll.removePollCallback
delay = timing.delay
wait = timing.wait
uSleep = timing.uSleep

# Keyboard Features
nameToKey = keyboard.nameToKey
keyToName = keyboard.keyToName
keyNames = keyboard.keyNames
setKeyboardCallback = keyboard.setKeyboardCallback

# Mouse Features
setMousePosition = mouse.setMousePosition
setMouseVisibility = mouse.setMouseVisibility
setMouseCallbacks = mouse.setMouseCallbacks
getMouseRange = mouse.getMouseRange

# Joystick Features
getJoystickFeatures = joystick.getJoystickFeatures
setJoystickCallbacks = joystick.setJoystickCallbacks

# Graphics Features
toggleFullscreen = graphics.toggleFullscreen
getFullscreen = graphics.getFullscreen
getResolution = graphics.getResolution
setVideoCaption = graphics.setVideoCaption
clearScreen = graphics.clearScreen
makeVideoChanges = graphics.makeVideoChanges
startVideo = graphics.startVideo
stopVideo = graphics.stopVideo
setGammaRamp = graphics.setGammaRamp
getShowFPS = graphics.getShowFPS


# EEG Features
if sys.platform=='darwin':
    AWCard = None #eeg.awCard
    LJCard = eeg.LabJack
    EPLPulseEEGException = eeg.EPLPulseEEGException
    AWCException = None #eeg.AWCException
else:
    Parallel = eeg.Parallel
    EEGShmAttached = eeg.shmAttached
    EEGShmAttach = eeg.shmAttach
    EEGShmDetach = eeg.shmDetach
    EEGRecStart = eeg.recStart
    EEGRecStop = eeg.recStop
    EEGGetOffset = eeg.getOffset
    EPLScalpEEGException = eeg.EPLScalpEEGException

# Sound Features
EPLSound = sound.EPLSound
SoundFile = sound.SoundFile

# VR Features

# GUI Features
