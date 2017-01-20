# PyEPL: hardware/vr/__init__.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This package provides abstracted access to Crystal Space's 3D world
rendering features.
"""

from avatar import LowVAvatarSpeedBubble
from eyes import LowVEye
#from ears import LowVEars
from environment import LowVEnvironment, setMaxFacetLength
from environment import SphereGeom, BoxGeom, PlaneGeom, Sphere, FloorBox, Sprite, SkyBox
from environment import BuildingBox

def initialize(**options):
    """
    """
    if options.has_key("max_facet_length"):
        setMaxFacetLength(options["max_facet_length"])

def finalize():
    """
    """
    pass
