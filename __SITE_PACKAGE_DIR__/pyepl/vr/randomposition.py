# PyEPL: vr/randomposition.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
"""

import random
import numpy
import math

class RPMutableSpace:
    """
    """
    def __init__(self, *shapes):
        """
        """
        self.shapes = list(shapes)
    def add(self, *shapes):
        """
        """
        self.shapes.extend(shapes)
    def remove(self, *shapes):
        """
        """
        for shape in shapes:
            self.shapes.remove(shape)
    def getTotalWeight(self):
        """
        """
        return sum(map(lambda x: x.getTotalWeight(), self.shapes))
    def generatePosition(self):
        """
        """
        return self.generatePositionAndSource()[0]
    def generatePositionAndSource(self):
        """
        """
        x = random.uniform(0.0, self.getTotalWeight())
        for shape in self.shapes:
            x -= shape.getTotalWeight()
            if x <= 0:
                return shape.generatePosition(), shape
        raise ValueError, "Space has zero weight."

class RPSpace:
    """
    """
    def getTotalWeight(self):
        """
        """
        return 0.0
    def generatePosition(self):
        """
        """
        raise ValueError, "Space has zero weight."
    #...

#...

class RPPoint(RPSpace):
    """
    """
    def __init__(self, weight, point):
        """
        """
        self.point = point
        self.weight = weight
    def getTotalWeight(self):
        """
        """
        return self.weight
    def generatePosition(self):
        """
        """
        return point
    #...

class RPLineSegment(RPSpace):
    """
    """
    def __init__(self, density, point1, point2):
        """
        """
        self.point = numpy.array(point1)
        self.vector = numpy.array(point2) - self.point
        self.weight = density * math.sqrt(numpy.sum(self.vector * self.vector))
    def getTotalWeight(self):
        """
        """
        return self.weight
    def generatePosition(self):
        """
        """
        return self.point + self.vector * random.random()
    #...

#...
