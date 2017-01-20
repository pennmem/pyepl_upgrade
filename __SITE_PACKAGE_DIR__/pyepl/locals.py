# PyEPL: locals.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module imports the most commonly used features of pyEPL.
Experimenters should include the line 'from pyepl.locals import *' at
the beginning of their experiments.
"""

import pyepl
from timing import now, wait
from display import Image
from display import Movie
from display import Font, setDefaultFont
from display import SolidBackground
from display import VideoTrack
from display import Color
from display import Text
from display import ABOVE, BELOW, LEFT, RIGHT, OVER, NORTH, NORTHEAST, EAST, SOUTHEAST, SOUTH, SOUTHWEST, WEST, NORTHWEST, CENTER
from display import CompoundStimulus
from sound import AudioClip, FileAudioClip, Beep
from sound import AudioTrack
from keyboard import KeyTrack, Key
from joystick import JoyTrack, JoyButton, JoyAxis, JoyHat, JoyBall
from mouse import MouseTrack, MouseButton, MouseAxis, MouseRoller
from textlog import LogTrack
from eeg import EEGTrack
from pool import Pool, PoolDict, TextPool, ImagePool, SoundPool
from vr import VRTrack
from vr.randomposition import * #...
from mechinput import * #...
from pyepl import initialize
from pyepl import finalize
from exputils import Experiment, EPLOption, PresentationClock, State
from convenience import setRealtime, instruct, getInstructing, instructBegin, instructStep, instructEnd, instructSeenAll, waitForAnyKey, buttonChoice, micTest, flashStimulus, presentStimuli, mathDistract,recognition
from optparse import make_option
from virtualtrack import VirtualTrack
from version import checkVersion, checkVersionRange
