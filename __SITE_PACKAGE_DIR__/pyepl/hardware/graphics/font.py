# PyEPL: hardware/graphics/font.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
Low level font access.
"""

import pygame
import pygame.surfarray
from pygame.locals import *
import image
import numpy

class LowFont:
    """
    Represents a loaded TrueType font.
    """
    def __init__(self, filename):
        """
        Create LowFont.
        """
        self.filename = filename
        self.size = None
        self.font = None
    def setSize(self, size):
        """
        """
        if size != self.size:
            self.font = pygame.font.Font(self.filename, size)
            self.size = size
    def write(self, text, size, color):
        """
        Render string text onto new LowImage with point size size.
        """
        self.setSize(size)
        img = self.font.render(text, True, (255, 255, 255))#.convert_alpha() for El Capitan
        if len(color) == 4 and color[3] != 1.0:
            alpha = pygame.surfarray.pixels_alpha(img)
            # changed the following from Numeric.UInt8
            alpha[:, :] = (alpha[:, :] * color[3]).astype(numpy.uint8) 
            del alpha
        pixels = pygame.surfarray.pixels3d(img)
        pixels[:, :, 0] = int(color[0] * 255)
        pixels[:, :, 1] = int(color[1] * 255)
        pixels[:, :, 2] = int(color[2] * 255)
        del pixels
        return image.LowImage(img)
    def getSize(self, text, size):
        """
        Return a 2-tuple of the x, y pixel size of text rendered in
        this font at point size size.
        """
        self.setSize(size)
        return self.font.size(text)
