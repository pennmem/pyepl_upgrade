# PyEPL: hardware/graphics/image.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides low level image manipulation and display
features.
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
try:
    from OpenGL.GLU import *
    GLU = 1
except:
    print "Warning: OpenGL.GLU did not import correctly."
    GLU = None

import pyepl.exceptions
import pyepl.hardware.graphics

# Image operations:
op_nop = 0
op_multiply = 1
op_divide = 2
op_add = 3
op_subtract = 4
op_scale = 5
op_slice = 6
op_negate = 7
op_apply = 8

class Color:
    """
    Represents an RGBA color.
    """
    def __init__(self, *args, **dargs):
        """
        Create an RGBA Color.  Parameters can be (red, green, blue),
        (red, green, blue, alpha), a simple color name, or an HTML hex
        color (i.e. #FFFFFF).  If the optional keyword parameter
        normtoone is present and False, the constructor expects values
        from 0 to 255 instead of between 0.0 and 1.0.
        """
        if len(args) == 1:
            if isinstance(args[0], Color):
                self.red = args[0].red
                self.green = args[0].green
                self.blue = args[0].blue
                self.alpha = args[0].alpha
                return
            elif isinstance(args[0], tuple):
                if len(args[0]) == 3:
                    red, green, blue = args[0]
		    if not dargs.has_key("normtoone") or dargs["normtoone"]:
			alpha = 1.0
		    else:
			alpha = 255
                else:
                    red, green, blue, alpha = args[0]
            elif isinstance(args[0], str):
                self.red, self.green, self.blue, self.alpha = pygame.color.Color(args[0])
                return
        elif len(args) == 3:
            red, green, blue = args
	    if not dargs.has_key("normtoone") or dargs["normtoone"]:
		alpha = 1.0
	    else:
		alpha = 255
        elif len(args) == 4:
            red, green, blue, alpha = args
        else:
            raise ValueError, "Invalid number of parameters for Color."
        if not dargs.has_key("normtoone") or dargs["normtoone"]:
            # print dargs.has_key("normtoone")
	    self.red = int(red * 255)
            self.green = int(green * 255)
            self.blue = int(blue * 255)
            self.alpha = int(alpha * 255)
        else:
            self.red = red
            self.green = green
            self.blue = blue
            self.alpha = alpha
        self.normalize()
    def __add__(self, x):
        """
        Add components of two colors.
        """
        if isinstance(x, Color):
            return Color(self.red + x.red, self.green + x.green, self.blue + x.blue, (self.blue + x.blue) / 2)
        else:
            return Color(self.red + x, self.green + x, self.blue + x, (self.blue + x.blue) / 2)
    def __sub__(self, x):
        """
        Subtract components of one color from another.
        """
        if isinstance(x, Color):
            return Color(self.red - x.red, self.green - x.green, self.blue - x.blue, (self.blue + x.blue) / 2)
        else:
            return Color(self.red - x, self.green - x, self.blue - x, (self.blue + x.blue) / 2)
    def __mul__(self, x):
        """
        Multiply colors.
        """
        if isinstance(x, Color):
            return Color(self.red * x.red, self.green * x.green, self.blue * x.blue, (self.blue + x.blue) / 2)
        else:
            return Color(self.red * x, self.green * x, self.blue * x, (self.blue + x.blue) / 2)
    def __div__(self, x):
        """
        Divide colors.
        """
        if isinstance(x, Color):
            return Color(self.red / x.red, self.green / x.green, self.blue / x.blue, (self.blue + x.blue) / 2)
        else:
            return Color(self.red / x, self.green / x, self.blue / x, (self.blue + x.blue) / 2)
    def __neg__(self):
        """
        Get complementary color.
        """
        return Color(255 - self.red, 255 - self.green, 255 - self.blue, self.alpha)
    def __len__(self):
        """
        Length is always three.
        """
        return 3
    def getTuple(self):
        """
        Get 4-tuple for color (as used in constructor).
        """
        return (self.red / 255.0, self.green / 255.0, self.blue / 255.0, self.alpha / 255.0)
    def normalize(self):
        """
        Ensure that none of the color components are out of range
        without modifying hue.
        """
        m = max(self.red, self.green, self.blue)
        if m != 0:
            f = 255.0 / m
            if f < 1.0:
                self.red *= f
                self.green *= f
                self.blue *= f
            if self.alpha > 255:
                self.alpha = 255
            elif self.alpha < 0:
                self.alpha = 0
    def __getitem__(self, index):
        """
        """
        if index == 0:
            return self.red
        if index == 1:
            return self.green
        if index == 2:
            return self.blue
        if index == 3:
            return self.alpha
        raise IndexError, "Color indeces must be 0, 1, 2, or 3."
    def __repr__(self):
        """
        """
        return "(%f, %f, %f, %f)" % (self.red / 255.0, self.green / 255.0, self.blue / 255.0, self.alpha / 255.0)

class OGLSprite:
    """Implement the ugly details of "blitting" to OpenGL"""
    def __init__(self, surf, mipmap=None):
        """OGLSprite(self, surf, mipmap=None) -> OGLSprite
        
        Create a drawable texture out of a given surface."""

        w, h = surf.get_width(), surf.get_height()
        w2, h2 = 1, 1
        while w2 < w: w2 <<= 1
        while h2 < h: h2 <<= 1

        img = pygame.Surface((w2, h2), SRCALPHA, 32)
        
        img.blit(surf, (0,0))
        rgba = pygame.image.tostring(img, "RGBA", 0)

        #assign a texture
        texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)

        if mipmap:
            if not GLU:
                raise NotImplementedError("OGLSprite mipmaps require OpenGL.GLU")
            #build MIPMAP levels. Ths is another slow bit            
            gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, w2, h2, GL_RGBA, GL_UNSIGNED_BYTE, rgba)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        else:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w2, h2, 0, GL_RGBA, GL_UNSIGNED_BYTE, rgba)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)  
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR) 

        self.mipmap = mipmap
        self.srcsize = w, h
        self.texsize = w2, h2
        self.coords = float(w)/w2, float(h)/h2
        self.texid = texid
    def __del__(self):
        """
        """
        try:
            glDeleteTextures([self.texid])
        except NameError:
            pyepl.exceptions.eplWarn("glDeleteTextures function not present.")
    def update(self, surf):
        """update(self, surf) -> None
        """
        if self.mipmap:
            raise TypeError("Cannot update a mipmap enabled OGLSprite")

        w, h = surf.get_width(), surf.get_height()
        w2, h2 = 1, 1
        while w2 < w: w2 <<= 1
        while h2 < h: h2 <<= 1

        img = pygame.Surface((w2, h2), SRCALPHA, surf)
        img.blit(surf, (0,0))
        rgba = pygame.image.tostring(img, "RGBA", 0)

        glBindTexture(GL_TEXTURE_2D, self.texid)
        if 'glTexSubImage2D' in dir() and w2 <= self.texsize[0] and h2 <= self.texsize[1]:

            # untested; i suspect it doesn't work
            w2, h2 = self.texsize
            glTexSubImage2D(GL_TEXTURE_RECTANGLE_EXT, 0,
                0, 0, w2, h2, GL_RGBA, GL_UNSIGNED_BYTE, rgba);
            if (w, h) != self.srcsize:
                self.coords = float(w)/w2, float(h)/h2
        else:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                w2, h2, 0, GL_RGBA, GL_UNSIGNED_BYTE, rgba)
            self.coords = float(w)/w2, float(h)/h2
            self.texsize = w2, h2

        self.srcsize = w, h

        #print "TEX", self.srcsize, self.texsize, self.coords
    def blit_at(self, *rects):
        """blit_at(self, *rects) -> self

        Draw the texture at the supplied position(s).  If a tuple and width and
        height are not specified, the original size is used (just like you'd
        expect).  Returns self so ogs.enter().blit().exit() works"""

        for rect in rects:
            x0, y0 = rect[0:2]
            try:
                x1, y1 = x0 + rect[2], y0 + rect[3]
            except IndexError:
                x1, y1 = x0 + self.srcsize[0] - 1, y0 + self.srcsize[1] - 1

            glBindTexture(GL_TEXTURE_2D, self.texid)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0, 0); glVertex2f(x0, y0)
            glTexCoord2f(self.coords[0], 0); glVertex2f(x1, y0)
            glTexCoord2f(0, self.coords[1]); glVertex2f(x0, y1)
            glTexCoord2f(self.coords[0], self.coords[1]); glVertex2f(x1, y1)
            glEnd()

        return self
    def enter(self, xres, yres):
        """enter(self) -> self
        
        Set up OpenGL for drawing textures; do this once per batch of
        textures.  Returns self so ogs.enter().blit().exit() works"""

        glViewport(0, 0, xres, yres)
        glPushAttrib(GL_ENABLE_BIT)     # save old enables
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glColor4f(1,1,1,1)
        glEnable(GL_TEXTURE_2D)

        # XXX: in pre pygame1.5, there is no proper alpha, so this makes
        # the entire texture transparent.  in 1.5 and forward, it works.
        if pygame.version.ver >= '1.4.9':
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        #glEnable(GL_ALPHA_TEST)
        #glAlphaFunc(GL_GREATER, 0.5)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, xres, yres, 0.0, 0.0, 1.0)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        #glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

        return self
    def exit(self):
        """exit(self) -> None

        Return OpenGL to previous settings; do this once per batch."""
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()
    def get_width(self):
        """get_width(self) -> int"""
        return self.srcsize[0]
    def get_height(self):
        """get_height(self) -> int"""
        return self.srcsize[1]

class LowImage:
    """
    Low level representation of an image.
    """
    def __init__(self, *args):
        """
        Create LowImage.
        """
        if len(args) == 2:
            self.surf = pygame.Surface(args)
        elif len(args) == 1:
            param = args[0]
            if isinstance(param, pygame.Surface):
                self.surf = param
            elif isinstance(param, str):
                self.surf = pygame.image.load(param)
            else:
                raise ValueError, "Invalid type for LowImage constructor argument."
        else:
            raise ValueError, "Invalid number of arguments for LowImage constructor."
        self.gl_texture = OGLSprite(self.surf)
        self.gl_texture_dirty = False

	# this next line supposedly breaks on OSX, set to none if this is the case
        #self.surfarray = pygame.surfarray.pixels3d(self.surf)
        # fix for the mac (breaks other stuff)
        self.surfarray = None
    def dataString(self):
        """
        Return an RGBA string of the image data.
        """
        return pygame.image.tostring(self.surf, "RGBA")
    def cleanGLTexture(self):
        """
        """
        if self.gl_texture_dirty:
            self.gl_texture.update(self.surf)
            self.gl_texture_dirty = False
    def show(self, x, y):
        """
        """
        self.cleanGLTexture()
        self.gl_texture.enter(*pygame.display.get_surface().get_size())
        self.gl_texture.blit_at((x, y))
        self.gl_texture.exit()
    def fill(self, r, g, b, a):
        """
        """
        self.surf = self.surf.convert_alpha()
        self.surf.fill((int(r), int(g), int(b), int(a)))
        self.gl_texture_dirty = True
    def __getitem__(self, index):
        """
        Two dimensional indexing and slicing.
        """
        return pygame.surfarray.make_surface(self.surfarray[index])
    def __setitem__(self, index, value):
        """
        Index and slice assignment.
        """
        if isinstance(value, LowImage):
            self.surfarray[index] = value.surfarray
        else:
            self.surfarray[index] = value
        self.gl_texture_dirty = True
    def __mul__(self, x):
        """
        Color multiplication.
        """
        if isinstance(x, LowImage):
            return pygame.surfarray.make_surface(self.surfarray * x.surfarray)
        else:
            return pygame.surfarray.make_surface(self.surfarray * x)
    def __div__(self, x):
        """
        Color division.
        """
        if isinstance(x, LowImage):
            return pygame.surfarray.make_surface(self.surfarray / x.surfarray)
        else:
            return pygame.surfarray.make_surface(self.surfarray / x)
    def __add__(self, x):
        """
        Color addition.
        """
        if isinstance(x, LowImage):
            return pygame.surfarray.make_surface(self.surfarray + x.surfarray)
        else:
            return pygame.surfarray.make_surface(self.surfarray + x)
    def __sub__(self, x):
        """
        Color subtraction.
        """
        if isinstance(x, LowImage):
            return pygame.surfarray.make_surface(self.surfarray - x.surfarray)
        else:
            return pygame.surfarray.make_surface(self.surfarray - x)
    def __neg__(self):
        """
        Color inversion.
        """
        return pygame.surfarray.make_surface(-self.surfarray)
    def scale(self, x, y):
        """
        Get scaled image.
        """
        return LowImage(pygame.transform.scale(self.surf, (x, y)))
    def getSize(self):
        """
        Return an x, y tuple for image dimensions.
        """
        return self.surf.get_size()
