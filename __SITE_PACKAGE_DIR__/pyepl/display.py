# PyEPL: display.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides graphics abstractions.
"""

import textlog
from base import Carvable, Track, Registered, MediaFile, UniquelyConstructed
import hardware
import timing
import threading
#import PIL.Image  # catch error here!
import os
import weakref
import exputils
from stimulus import Stimulus

import pygame

# Get the PyEPL directory (used below to find the default font)
pyepldir = os.path.abspath(os.path.dirname(__file__))

# Use the Color class from the hardware.graphics.image module
Color = hardware.graphics.image.Color

# Define positional relations:
NORTH = 0
NORTHEAST = 1
EAST = 2
SOUTHEAST = 3
SOUTH = 4
SOUTHWEST = 5
WEST = 6
NORTHWEST = 7
CENTER = 8

BELOW = 9
ABOVE = 10
LEFT = 11
RIGHT = 12
OVER = 13


class Showable:
    """
    An object which may be displayed in the basic video output layer.
    """
    def __init__(self):
        self.loadRequireCount = 0
    def requireLoaded(self):
        self.loadRequireCount += 1
        if not self.isLoaded():
            self.load()
    def unrequireLoaded(self):
        self.loadRequireCount -= 1
        if self.loadRequireCount < 0:
            self.loadRequireCount = 0
        if self.loadRequireCount == 0 and \
                self.isLoaded() and \
                (hasattr(self,'filename') and not self.filename is None):
            self.unload()
    def show(self, x, y):  # to be overridden
        """
        Draw this object.
        """
        pass
    def getSize(self):  # to be overridden
        """
        Return a 2-tuple representing the X and Y dimensions of this
        showable in pixels.
        """
        return (0, 0)
    def logLine(self):  # to be overridden
        """
        Log the object.
        """
        return "SHOWABLE"
    def isLoaded(self):
        """
        Returns true if the showable is loaded in memory, otherwise returns false.
        """
        return True
    def load(self):
        """
        Loads the object into memory.
        """
        pass
    def unload(self):
        """
        Unloads the object from memory.
        """
        pass

class Shown:
    """
    Instances of this class are meant to act as unique identifiers for
    an instance of a showable on the screen.  They also provide
    information for the size and placement of the showable, as well as
    a dictionary of anchor points (anchor[NORTH], anchor[SOUTHWEST],
    ...) for use in placing other showables.
    """
    def __init__(self, x, y, width, height):
        """
        Create a shown object.
        """
        # set up the values
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # calculate the anchors
        self.anchor = {}
        self.anchor[CENTER] = (x + (width / 2), y + (height / 2))
        self.anchor[NORTH] = (x + (width / 2), y)
        self.anchor[NORTHEAST] = (x + width, y)
        self.anchor[EAST] = (x + width, y + (height / 2))
        self.anchor[SOUTHEAST] = (x + width, y + height)
        self.anchor[SOUTH] = (x + (width / 2), y + height)
        self.anchor[SOUTHWEST] = (x, y + height)
        self.anchor[WEST] = (x, y + (height / 2))
        self.anchor[NORTHWEST] = (x, y)

class ActiveShowable(Showable):
    """
    Showable that must be continually refreshed.
    """
    def logLine(self):  # to be overridden
        """
        Log the object.
        """
        return "ACTIVESHOWABLE"

class Image(UniquelyConstructed, Carvable, Showable, Stimulus):
    """
    Represents an image.
    """
#    def __uinit__(self, x, propxsize = 0.5, propysize = 0.5):
    def __uinit__(self, x, propxsize = None, propysize = None):
        """
        Creates a new Image object.

        INPUT ARGS:
          x- Data used to construct Image. Can be the filename of an image file, or a LowImage object.
          propxsize- (optional) size of the X dimension of the Image.  specified as a fraction of the Y dimension of the screen.
          propysize- (optional) size of the y dimension of the Image.  specified as a fraction of the Y dimension of the screen.          
        ...
        """
        Carvable.__init__(self)
        Showable.__init__(self)
        
        # save the proportional dimensions...
        self.propxsize = propxsize
        self.propysize = propysize
        
        if isinstance(x, hardware.graphics.LowImage):
            # if the parameter is a LowImage object, just wrap it
            self.img = x
            self.img_unscaled = x
            self.filename = None
        else:
            # otherwise, assume it's a filename
            self.filename = x
            self.img = None
            self.img_unscaled = None

        # set empty logline
        self.logLineStr = 'IMAGE'

    def getLow(self):
        """
        Returns the LowImage object associated with this Image.

        OUTPUT ARGS:
          r- a reference to the new LowImage object.
        """
        if self.img:
            # if it's loaded, just return it
            return self.img
        
        # otherwise, load it, unload it (keeping a reference), and return it
        self.load()
        r = self.img
        self.unload()
        return r
    def getLowUnscaled(self):
        """
        """
        if self.img:
            return self.img_unscaled
        self.load()
        r = self.img_unscaled
        self.unload()
        return r
    def load(self):
        """
        After calling this method, the image data is gauranteed to be
        loaded into primary memory.

        If keepLoadedAfterSmartShow is set to True, the image will not
        be unloaded after it is shown with SmartShow.
        """
        if not self.img:
            # if it's not already loaded, load it by constructing a LowImage object...

            # if there are no proportional dimensions...
            if self.propxsize is None or self.propysize is None:
                # construct the LowImage without scaling
                self.img = hardware.graphics.LowImage(self.filename)

                # set the unscaled image to be the normal one
                self.img_unscaled = self.img

                # and we're done
                return

            # try to get the VideoTrack
            v = VideoTrack.lastInstance()

            # if there is a VideoTrack...
            if v:
                # get the screen's vertical resolution
                yres = v.getResolution()[1]

                # calculate the pixel dimensions for the image based on the vertical resolution and the proportional dimensions
                xs = int(yres * self.propxsize)
                ys = int(yres * self.propysize)
                
                # construct the LowImage
                self.img_unscaled = hardware.graphics.LowImage(self.filename)

                # scale it
                self.img = self.img_unscaled.scale(xs, ys)
            else:
                # no VideoTrack...

                # construct the LowImage without scaling
                self.img = hardware.graphics.LowImage(self.filename)

                # set the unscaled image to be the normal one
                self.img_unscaled = self.img

                # set the proportional dimensions to None...
                self.propxsize = None
                self.propysize = None
    def unload(self):
        """
        After calling this method, the Image's data is unloaded from memory.
        """
        # unload by removing our internal reference to the LowImage object
        self.img = None
        self.img_unscaled = None
    def isLoaded(self):
        """
        Checks if this object is actually loaded into memory.

        OUTPUT ARGS:
          b- True if the object is loaded in memory, False if not.
        """
        # check whether or not it's loaded by seeing if we have an internal reference to a LowImage object
        return not self.img is None
    def __getstate__(self):
        """
        Don't give the image data to pickle.
        """
        # remove the LowImage object before pickle looks at the data (because LowImages are not picklable)
        d = self.__dict__.copy()
        del d["img"]
        try:
            del d["img_unscaled"]
        except KeyError:
            pass
        return d
    def __setstate__(self, state):
        """
        After unpickling, the image is NOT loaded.
        """
        # unpickle with None as self.image (since we left it out when we pickled)
        self.__dict__.update(state)
        self.img = None
    def export(self, archive, namehint):
        """
        Export image.
        """
        pass #...
    def setLogLine(self):
        """
        Set the ID for the video log.

        XXX IMPORTANT XXX
        We will eventually have to call this every time the image is changed.
        XXX IMPORTANT XXX
        """
        # get the image's pixel size
        xs, ys = self.getSize()

        # return the log line
        self.logLineStr = "IMAGE\t%s\t%d\t%d" % (self.filename, xs, ys)
    def logLine(self):
        """
        Identify this image for the video log.
        """
        return self.logLineStr
    def __getitem__(self, index):
        """
        Two dimensional indexing and slicing.
        """
        # make sure it's loaded first
        self.load()
            
        # index or slice the LowImage
        r = self.img[index]

        # if we get a LowImage back, wrap it with a new Image object and return that
        if isinstance(r, hardware.graphics.LowImage):
            return Image(r)

        # otherwise, return the color value we got from it
        return r

    def __setitem__(self, index, value):
        """
        Index and slice assignment.
        """
        # make sure the image is not "carved in stone"
        self.aboutToChange()

        # make sure it's loaded already
        self.load()
        
        # Set the value or slice in the LowImage
        self.img[index] = value
    def __mul__(self, x):
        """
        Color multiplication.
        """
        # make sure the image is loaded
        self.load()
        
        # multiply the LowImages and return the result wrapped in an Image object
        return Image(self.img * x)
    def __div__(self, x):
        """
        Color division.
        """
        # make sure the image is loaded
        self.load()

        # divide the LowImages and return the result wrapped in an Image object
        return Image(self.img / x)
    def __add__(self, x):
        """
        Color addition.
        """
        # make sure the image is loaded
        self.load()
        
        # add the LowImages and return the result wrapped in an Image object
        return Image(self.img + x)
    def __sub__(self, x):
        """
        Color subtraction.
        """
        # make sure the image is loaded
        self.load()

        # subtract the LowImages and return the result wrapped in an Image object
        return Image(self.img - x)
    def __neg__(self):
        """
        Color inversion.
        """
        # make sure the image is loaded
        self.load()
        
        # negate the LowImages and return the result wrapped in an Image object
        return Image(-self.img)
    def scale(self, x, y):
        """
        Rescales the image to the specified x, y proportions of the screen.
        """
        # make sure the image is loaded
        self.load()

        # try to get the VideoTrack
        v = VideoTrack.lastInstance()

        # if there is a VideoTrack...
        if v:
            # get the screen's vertical resolution
            yres = v.getResolution()[1]
            
            # calculate the pixel dimensions for the image based on the vertical resolution and the proportional dimensions
            xs = int(yres * x)
            ys = int(yres * y)

        # scale the LowImages and return the result wrapped in an Image object
        return Image(self.img_unscaled.scale(int(xs), int(ys)), x, y)
    def apply(self, f):
        """
        Apply function f to all pixels of image for result.  f can
        accept just a Color or a Color and and x, y tuple for
        position.
        """
        # make sure the image is loaded
        self.load()

        # apply the LowImage and function and return the result wrapped in an Image object
        return Image(self.img.apply(x))
    def getSize(self):
        """
        Return an x, y tuple for image dimensions.
        """
        # make sure the image is loaded
        self.load()
        
        # return the size of the LowImage
        return self.img.getSize()
    def show(self, x, y):
        """
        Put this image on the screen at x, y.
        """
        # make sure the image is loaded
        self.load()
        
        # have the LowImage draw itself at the specified coordinates
        self.img.show(x, y)

        # set the logLine
        self.setLogLine()

    def present(self, clk = None, duration = None, jitter = None, bc = None, minDuration = None):
        """
        Present an image on the screen.  If a ButtonChooser is
        provided, present ignores the jitter and clears the stimulus
        once a button is pressed or the duration waiting for a
        response is exceeded.

        INPUT ARGS:
          clk- Optional PresentationClock to update.
          duration/jitter- Duration to display the stimulus.
          bc- Optional ButtonChooser object.
          minDuration- Used in combination with bc to specify a minimum
                       time that a stimulus must be presented before a
                       keypress to the bc is accepted.
          
        OUTPUT ARGS:
          timestamp- time and latency of when the image came on the screen.
          button- Button pressed if we passed in bc.
          bc_time- Time and latency of when the button was pressed (if provided)
        """

        v = VideoTrack.lastInstance()
        
        # get the clock if needed
        if clk is None:
            clk = exputils.PresentationClock()

        # show the image
        t = v.showCentered(self)
        timestamp = v.updateScreen(clk)

        if bc:
            # wait for button press
            button,bc_time = bc.waitWithTime(minDuration,duration,clk)
        else:
            clk.delay(duration,jitter)

        # unshow that image
        v.unshow(t)
        v.updateScreen(clk)

        if bc:
            return timestamp,button,bc_time
        else:
            return timestamp


# New Movie Class
class Movie(UniquelyConstructed, Showable, Stimulus):
    """
    Represents a movie.  In PyEPL, movies are rendered onto an image
    surface, which you must first show (via one of the many show
    methods in the VideoTrack).

    Once a movie surface is shown, you can start and stop playback
    with the playMovie and stopMovie methods of the VideoTrack.

    When you are done playing a movie, you can then unshow the image
    where the movie was projected.
    """
    def __uinit__(self, x):
        """
        Creates a new Movie object.  It uses pygame to play the movie,
        so it only supports mpg files.

        INPUT ARGS:
          x- Data used to construct Movie.
             Can be the filename of an movie file,
             or a pygame.movie.Movie object.
        ...
        """
        Showable.__init__(self)

        if isinstance(x, pygame.movie.MovieType):
            # if the parameter is a Movie object, just wrap it
            self.movie = x
            self.filename = None
            self.img = None
        else:
            # otherwise, assume it's a filename
            self.filename = x
            self.movie = None
            self.img = None
        
        # set empty logline
        self.logLineStr = 'MOVIE'

    def load(self):
        """
        After calling this method, the image data is gauranteed to be
        loaded into primary memory.

        If keepLoadedAfterSmartShow is set to True, the image will not
        be unloaded after it is shown with SmartShow.
        """
        if self.movie is None:
            # create the movie instance
            self.movie = pygame.movie.Movie(self.filename)

        if self.img is None:
            # Create a surface where pygame will render the movie
            self._render_surf = pygame.Surface(self.movie.get_size())

            # Tell the movie to render frames to that new surface
            self.movie.set_display(self._render_surf)

            # Create a LowImage for performing the OpenGL blitting of the
            # movie frames to the actual OpenGL surface that we use
            self.img = hardware.graphics.LowImage(self._render_surf)
    def unload(self):
        """
        After calling this method, the Movie's data is unloaded from memory.
        """
        # stop playing if we are
        self.stop()
        
        # unload by removing our internal reference to the LowImage object
        self._render_surf = None
        self.img = None
        self.movie = None
        
    def isLoaded(self):
        """
        Checks if this object is actually loaded into memory.

        OUTPUT ARGS:
          b- True if the object is loaded in memory, False if not.
        """
        # check whether or not it's loaded by seeing if we have an
        # internal reference to a LowImage object
        return not self.img is None
    
    def __getstate__(self):
        """
        Don't give the image data to pickle.
        """
        # remove the Movie and LowImage objects before pickle looks at
        # the data (because LowImages are not picklable)
        d = self.__dict__.copy()
        for todel in ['img','movie','_render_surf']:
            try:
                del d[todel]
            except KeyError:
                pass
        return d
    def __setstate__(self, state):
        """
        After unpickling, the movie is NOT loaded.
        """
        # unpickle with None as self.image (since we left it out when
        # we pickled)
        self.__dict__.update(state)
        self.img = None
        self.movie = None
        self._render_surf = None

    def export(self, archive, namehint):
        """
        Export image.
        """
        raise NotImplementedError #...
    def setLogLine(self):
        """
        Set the ID for the video log.

        XXX IMPORTANT XXX
        We will eventually have to call this every time the movie is changed.
        XXX IMPORTANT XXX
        """
        # get the movie's pixel size
        xs, ys = self.getSize()

        # return the log line
        self.logLineStr = "MOVIE\t%s\t%d\t%d\t%d" % \
                          (self.filename, xs, ys, self.getTotalTime())
    def logLine(self):
        """
        Identify this movie for the video log.
        """
        return self.logLineStr
    def getSize(self):
        """
        Return an x, y tuple for movie dimensions.
        """
        # make sure the image is loaded
        self.load()
        
        # return the size of the LowImage
        return self.img.getSize()
    def show(self, x, y):
        """
        Put this image on the screen at x, y.
        """
        # make sure the image is loaded
        self.load()

        # see if we have to update the frame
        if self.hasNewFrame():
            self._updateFrame()
        
        # have the LowImage draw itself at the specified coordinates
        self.img.show(x, y)

        # set the logLine
        self.setLogLine()

    def hasNewFrame(self):
        """
        See if the movie has a new frame ready.
        """
        if not self.isLoaded():
            self.load()
            
        return self.movie.get_frame() != self._prevFrame
            
    def _updateFrame(self):
        """
        Update the surface with the current movie frame.
        """
        # set the gl_texture to be dirty so it can be updated
        self.img.gl_texture_dirty = True

        # clean the image to which the movie will render
        # this will render the new frame to the surface
        self.img.cleanGLTexture()

        # save the current frame
        self._prevFrame = self.movie.get_frame()
        

    def play(self,loops=0):
        
        # make sure we are loaded
        self.load()

        # reset the previous frame
        self._prevFrame = None
        self._latest_timestamp = None
        
        # start playing
        self.movie.play()
                
    def pause(self):
        # only pause if was running
        if self.movie and self.movie.get_busy():
            # pause it
            self.movie.pause()
#             # remove the playing callback
#             removePollCallback(self._playMovieCallback)

    def stop(self):
        # stop the movie if playing
        if self.movie and self.movie.get_busy():
            self.movie.stop()

#         # remove the poll callback
#         removePollCallback(self._playMovieCallback)

        # reset the previous frame
        self._prevFrame = None
        
    def getCurrentFrame(self):
        if self.movie:
            return self.movie.get_frame()
        
    def getElapsedTime(self):
        if self.movie:
            return long(self.movie.get_time()*1000)
        
    def getTotalTime(self):
        if self.movie:
            return long(self.movie.get_length()*1000)

    def getRemainingTime(self):
        if self.movie:
            return long((self.movie.get_length() -
                         self.movie.get_time())*1000)

    def present(self, clk = None, duration = None, jitter = None, bc = None, minDuration = None):
        """
        Present an movie on the screen.  If a ButtonChooser is
        provided, present ignores the jitter and clears the stimulus
        once a button is pressed or the duration waiting for a
        response is exceeded.

        INPUT ARGS:
          clk- Optional PresentationClock to update.
          duration/jitter- Duration to display the stimulus.
          bc- Optional ButtonChooser object.
          minDuration- Used in combination with bc to specify a minimum
                       time that a stimulus must be presented before a
                       keypress to the bc is accepted.
          
        OUTPUT ARGS:
          timestamp- time and latency of when the movie came on the screen.
          button- Button pressed if we passed in bc.
          bc_time- Time and latency of when the button was pressed (if provided)
        """

        v = VideoTrack.lastInstance()
        
        # get the clock if needed
        if clk is None:
            clk = exputils.PresentationClock()

        # do the auto delay if no duration is provided
        if not bc and not duration:
            doDelay = True
        else:
            doDelay = False
        # show the image
        shown_movie = v.showCentered(self)
        # show the movie
        timestamp = v.playMovie(self,t=clk,doDelay=doDelay)

        if bc:
            # wait for button press
            button,bc_time = bc.waitWithTime(minDuration,duration,clk)
        elif duration:
            clk.delay(duration,jitter)

        # stop the movie
        v.stopMovie(self,t=clk)
        
        # unshow that image
        v.unshow(shown_movie)
        v.updateScreen(clk)

        if bc:
            return timestamp,button,bc_time
        else:
            return timestamp



class Font(MediaFile):
    """
    Represents a graphical font.
    """
    def __init__(self, filename):
        """
        Create font object from TrueType font file.
        """
        # save the filename
        self.filename = filename

        # while the font is not loaded, self.font is None
        self.font = None
    def load(self):
        """
        After this call, the font is guaranteed to be loaded into
        primary memory.
        """
        if not self.font:
            # if it's not loaded already, set self.font to a LowFont object from the saved filename
            self.font = hardware.graphics.LowFont(self.filename)
    def unload(self):
        """
        """
        # remove the internal reference to the LowFont object
        self.font = None
    def isLoaded(self):
        """
        """
        # do we have a LowFont object?
        return bool(self.font)
    def __getstate__(self):
        """
        Don't give the internal font object to pickle.
        """
        # LowFont objects are not picklable, so we remove them before pickle does its thang
        d = self.__dict__.copy()
        del d["font"]
        return d
    def __setstate__(self, state):
        """
        After unpickling, the font is NOT loaded.
        """
        # since we excluded self.font from the pickle, we need to set self.font to None when we unpickle
        self.__dict__.update(state)
        self.font = None
    def export(self, archive, namehint):
        """
        Export font.
        """
        pass #...
    def write(self, text, size, color):
        """
        Return an object representing a rendition of the string text
        with the specified size and color in this font.
        """
        # return a text object
        return Text(text, self, size, color)
    def wordWrap(self, text, size, color, width):
        """
        Like write, but instead return a list of text objects where
        each item represents a line with text word wrapped to width.
        """
        # make sure we can access the global variables dealing with font defaults
        global defaultFont
        global defualtFontSize
        global defaultFontColor
        
        # use font defaults where needed
        if color:
            color = Color(color)
        else:
            color = defaultFontColor
        if not size:
            size = defaultFontSize

        # calculate the font size in pixels (from its proportional size)
        truesize = int(VideoTrack.lastInstance().getResolution()[1] * size)

        # make sure the font is loaded
        self.load()

        # split up the text by paragraph breaks
        para = text.split("\n\n")

        # start a list of paragraphs
        paragraphs = []

        # for each paragraph (between paragraph breaks)...
        for p in para:
            # remove leading and trailing white space and replace newlines with spaces
            p = p.lstrip().rstrip().replace("\n", " ")

            # if there anything left after that...
            if len(p):
                # start a list of words in the paragraph
                words = []

                # split up the paragraph at spaces
                for word in p.split(" "):
                    # for each resulting string that's not empty...
                    if len(word):
                        # add the word to the word list
                        words.append(word)

                # add the word list to the paragraph list
                paragraphs.append(words)

        # start a list to hold the text objects
        result = []

        # iterate over the paragraphs (each one is a list of words)...
        for words in paragraphs:
            # start with the first word of the paragraph
            wordbase = 0

            # set the limit to the length of the paragraph (in words)
            wordlimit = len(words)

            # as long as we haven't placed all the words yet...
            while wordbase != wordlimit:
                # construct a string - a potential line
                line = " ".join(words[wordbase : wordlimit])

                # find out how long it would be if we rendered it
                lwidth, lheight = self.font.getSize(line, truesize)
                if lwidth > width:
                    # if it's to big for our width, take off one of the words and try again
                    wordlimit -= 1
                else:
                    # otherwise, append the appropriate Text object to the result
                    result.append(Text(line, self, size, color))

                    # reset the word base so only the remaining words of the paragraph will be placed
                    wordbase = wordlimit

                    # reset the word limit so the rest of the paragraph will be placed
                    wordlimit = len(words)

            # add a blank line after each paragraph
            result.append(Text("", self, size, color))

        # return the lines
        return result

# create the initial font defaults...
defaultFont = Font("/Library/Fonts/DejaVuSans.ttf")
defaultFontSize = 0.0625
defaultFontColor = Color("white")

def setDefaultFont(font = None, size = None, color = None):
    global defaultFont
    global defaultFontSize
    global defaultFontColor

    # set the defaults given...
    if font:
        defaultFont = font
    if size:
        defaultFontSize = size
    if color:
        defaultFontColor = color

class Text(Showable, Stimulus):
    """
    Represents a string of text rendered with a certain font, color,
    and size.
    """
    def __init__(self, text, font = None, size = None, color = None):
        """
        Create text object.
        """
        # make sure we can access the global variables dealing with font defaults
        global defaultFont
        global defualtFontSize
        global defaultFontColor
		
        Showable.__init__(self)
        
        # split the text into lines
        self.text = text.split("\n")

        # use the font defaults where needed...
        if color:
            self.color = Color(color)
        else:
            self.color = defaultFontColor
        if not size:
            self.propsize = defaultFontSize
        else:
            self.propsize = size
        if font:
            self.font = font
        else:
            self.font = defaultFont
            
        # set the rendered text to None (not rendered)
        self.rendered = None
    def __getstate__(self):
        """
        Don't give the rendered form to pickle.
        """
        # remove the LowImage object before pickle looks at the data (because LowImages are not picklable)
        d = self.__dict__.copy()
        del d["rendered"]
        return d
    def __setstate__(self, state):
        """
        After unpickling, the text should NOT be rendered.
        """
        # unpickle with None as self.image (since we left it out when we pickled)
        self.__dict__.update(state)
        self.rendered = None
    def render(self):
        # make sure the font is loaded
        self.font.load()

        # calculate the pixel size of the text (from the given proportional size)
        self.size = int(VideoTrack.lastInstance().getResolution()[1] * self.propsize)
        
        # start rendered as an empty list
        self.rendered = []
        
        # for each line of text...
        for t in self.text:
            # ...append the rendered line
            self.rendered.append(self.font.font.write(t, self.size, self.color.getTuple()))
    def unrender(self):
        """
        Delete all the rendered text.
        """
        self.rendered = []
    def load(self):
        """
        Wrapper to render.
        """
        self.render()

    def unload(self):
        """
        Wrapper to unrender.
        """
        self.unrender()

    def isLoaded(self):
        """
        Tell if the text is rendered.
        """
        return bool(self.rendered)
        
    def show(self, x, y):
        """
        Draw the image on the screen.
        """
        # if the text isn't yet rendered...
        if not self.rendered:
            self.render()
            
        # get the size of the rendered text
        xsize, ysize = self.getSize()

        # calculate the horizontal center of the text area
        xplushalfxsize = x + (xsize / 2)

        # for each rendered line of text...
        for i in self.rendered:
            # get the size of the line
            ixsize, iysize = i.getSize()

            # show the line in a position such that it is horizontally centered in the text area
            i.show(xplushalfxsize - (ixsize / 2), y)

            # move the y position down the correct amount for the next line
            y += iysize

    def setXYSize(self):
        if self.rendered:
            # if it's been rendered, we'll get the size from the LowImage objects...
            self.xsize = 0
            self.ysize = 0
            for i in self.rendered:
                # iterate through the LowImage objects, getting the sum of y sizes and the maximum of x sizes
                x, y = i.getSize()
                self.xsize = max(self.xsize, x)
                self.ysize += y
        else:
            # in it hasn't been rendered...
            # make sure the font is loaded
            self.font.load()
            self.xsize = 0
            self.ysize = 0
            for t in self.text:
                # iterate through the lines of text, getting the sum of y sizes and the maximum of x sizes
                # we query the font object for how large the text would be if rendered
                x, y = self.font.font.getSize(t, self.size)
                self.xsize = max(self.xsize, x)
                self.ysize += y
        return self.xsize, self.ysize
    
    def getSize(self):
        """
        Return x, y dimensions of text.
        """
        try:
            # if we've already calculated the size of the text, just return it
            return self.xsize, self.ysize
        except AttributeError:
            # othersize...
            self.render()
            return self.setXYSize()
        
    def setColor(self, color):
        #set the color
        self.color = Color(color)
        #re-render
        self.render()

    def setSize(self, size):
        self.propsize = size
        self.render()
        self.setXYSize()

    def setFont(self, font):
        self.font = font
        self.render()
        self.setXYSize()
            
    def logLine(self):
        """
        Identify this text for the video log.
        """
        return "TEXT\t%s\t%d\t%s\t%r" % (self.font.filename, self.size, self.color, "\n".join(self.text))


    def present(self, clk = None, duration = None, jitter = None, bc = None, minDuration = None):
        """
        Present an text on the screen.  If a ButtonChooser is
        provided, present ignores the jitter and clears the stimulus
        once a button is pressed or the duration is exceeded.

        INPUT ARGS:
          clk- Optional PresentationClock to update.
          duration/jitter- Duration to display the stimulus.
          bc- Optional ButtonChooser object
          
        OUTPUT ARGS:
          timestamp- time and latency of when the text came on the screen.
          button- Button pressed if we passed in bc.
          bc_time- Time and latency of when the button was pressed (if provided)

        """

        v = VideoTrack.lastInstance()
        
        # get the clock if needed
        if clk is None:
            clk = exputils.PresentationClock()

        # show the image
        t = v.showCentered(self)
        timestamp = v.updateScreen(clk)

        if bc:
            # wait for button press
            button,bc_time = bc.waitWithTime(minDuration,duration,clk)
        else:
            clk.delay(duration,jitter)

        v.unshow(t)
        v.updateScreen(clk)

        if bc:
            return timestamp,button,bc_time
        else:
            return timestamp


class CompoundStimulus(Stimulus):
    """ 
    Comibine multiple stimuli into a single compound stimulus that you
    can present at once.  
    """
    def __init__(self,stimuli):
	"""
	stimuli = [(Name,[Text,Image],[ABS,PROP,REL],[LOC,(Relation,Name)]), ...]

	Create a CompoundStimulus object, which groups a set of showable objects.

	The constructor taks a single argument, which is a list of 4-tuples.

	The 4-tuples are of the form: 
	string-label, stimulus-object, location-specification-mode, location.

	The string-label can be any string.

	The stimulus-object can be an instance of Text or Image.

	Location-specification-mode can be one of: 'ABS', 'PROP', and 'REL'.

	The form of the location field will depend on the value of
	location-specification-mode.  

	If location-specification-mode is 'ABS', then the fourth field
	must be a 2-tuple containing the x- and y-coordinates (in
	pixels) for displaying the the showable.

	If location-specification-mode is 'PROP', then the fourth field
	must be a 2-tuple containing the x- and y screen fractions for
	displaying the the showable (e.g., (.6, .1) puts the showable
	3/5ths of the way from the left edge, and 1/10th down from the
	top edge).  

	If location-specification-mode is 'REL', the fourth field must
	be a 2- (or 3-) tuple whose first dimension contains the one
	of the relations: BELOW, ABOVE, LEFT, RIGHT, OVER.  The second
	dimension of must be the text-label of another showable in the
	list.  The (optional) 3rd dimension is used as the offset to
	adjust the relational location.  The first stimulus in the
	list can not be displayed using relative
	location-specification.
	
	If location-specification-mode is 'ANCHOR', the fourth field
	must be a 2- (up to 4-) tuple specifying first, the anchor on
	the stim to show with CENTER, NORTH, NORTHWEST, ..., second,
	the relative starting position as a 2-tuple of an (x,y)
	location or the text-label and anchor point of a shown
	('jubba',NORTHEAST).  You can optionally provide an offset in
	proportional units or pixels as the third part of the tuple,
	but the fourth part must be set to False if you want to provide
	the offset in pixels and not proportional units.

	('cool',stim,'ANCHOR',(CENTER, propToPixel(.25,.75), (.1,.15), True))
	
	Example:
	"""
	self.stimuli = stimuli

    def show(self):
	# loop and show the stimuli, keeping track of the showns in a
	# dictionary referenced by Name
	self.showns = {}
	v = VideoTrack.lastInstance()
	for label, stim, specMode, location in self.stimuli:
	    if specMode=='ABS':
		self.showns[label] = v.show(stim, location[0], location[1])
	    elif specMode=='PROP':
		self.showns[label] = v.showProportional(stim, location[0], location[1])
	    elif specMode=='REL':
		# check that relatum-label exists
		relatum = location[1]
		if relatum not in self.showns.keys():
		    raise ValueError, "Invalid target for relative location: " % relatum
		if len(location)==2:
		    self.showns[label] = v.showRelative(stim, location[0], self.showns[relatum])
		elif len(location)==3:
		    self.showns[label] = v.showRelative(stim, location[0], self.showns[relatum], location[2])
	    elif specMode=='ANCHOR':
		# get the anchor of the stim		
		anchor = location[0]

		# determine the relative position
		relPos = location[1]
		if type(relPos[0]) is str:
		    # must determine based on a shown and 
		    relPos = self.showns[relPos[0]].anchor[relPos[1]]

		# see about offset and isProportional
		offset = (0,0)
		isProp = True
		if len(location) > 2:
		    offset = location[2]
		    if len(location) > 3:
			isProp = location[3]

		# show the showable with all the anchor info
		self.showns[label] = v.showAnchored(stim, anchor, relPos, offset, isProp)
	    else:
		raise ValueError, "Invalid location specification mode %s" % specMode

    def unshow(self):
	v = VideoTrack.lastInstance()
	# loop and unshow the showns
	keyslist = self.showns.keys()
	for key in keyslist:
	    v.unshow(self.showns[key])

    def present(self, clk = None, duration = None, jitter = None, bc = None, minDuration = None):
        """
        Present a CompoundStimulus on the screen.  If a ButtonChooser is
        provided, present ignores the jitter and clears the stimulus
        once a button is pressed or the duration is exceeded.

        INPUT ARGS:
          clk- Optional PresentationClock to update.
          duration/jitter- Duration to display the stimulus.
          bc- Optional ButtonChooser object
          
        OUTPUT ARGS:
          timestamp- time and latency of when the text came on the screen.
          button- Button pressed if we passed in bc.
          bc_time- Time and latency of when the button was pressed (if provided)

        """

        v = VideoTrack.lastInstance()
        
        # get the clock if needed
        if clk is None:
            clk = exputils.PresentationClock()

	self.show()
        timestamp = v.updateScreen(clk)

        if bc:
            # wait for button press
            button,bc_time = bc.waitWithTime(minDuration,duration,clk)
        else:
            clk.delay(duration,jitter)

	self.unshow()
        v.updateScreen(clk)

        if bc:
            return timestamp,button,bc_time
        else:
            return timestamp

    
class SolidBackground(Showable):  # change this to handle any rectangular region
    """
    Draw the same color to every pixel on the screen regardless of
    showing position.
    """
    def __init__(self, color):
        """
        Create SolidBackground object.
        """
        Showable.__init__(self)
        
        # save the color
        self.color = color
 
    def show(self, x, y):
        """
        Clear the screen to the correct color.
        """
        # paint the whole screen with the saved color
        hardware.clearScreen(self.color)
    def logLine(self):
        """
        Log the background color.
        """
        return "BG\t%s" % (self.color,)

class VideoTrack(textlog.LogTrack):
    """
    A track for video output.
    """
    # set the track's registry info...
    logExtension = ".vidlog"
    trackTypeName = "VideoTrack"
    def __init__(self, basename, archive = None, autoStart = True):
        """
        Create the VideoTrack.
        """
        # call the LogTrack constructor
        textlog.LogTrack.__init__(self, basename, archive, autoStart)

        # list of things that should be displayed when the screen is next updated
        self.pending = []

        # list of things on the screen now
        self.onscreen = []

        # number of active showables represented in the onscreen list
        self.activepending = 0

        # default to no minimum frame duration (no maximum framerate)
        self.minframeduration = 0L

        # initialize the last_updated timestamp
        self.last_updated = (0L, 0L)

        # start with no update callbacks
        self.update_callbacks = []

        # list of calls to make after the screen is updated
        self.do_after_update = []

        # list of currently playing movies
        self._playing_movies = []

    def startLogging(self):
        """
        Begin logging all basic video output.
        """
        # call the LogTrack's startLogging method
        textlog.LogTrack.startLogging(self)

        # log the current resolution
        self.logResolution()
    def startService(self):
        """
        Initialize video output.
        """
        # create the window
        hardware.startVideo()

        # save the resolution
        self.screensize = hardware.getResolution()
        
        self.showFPS = hardware.getShowFPS()
    def stopService(self):
        """
        Finalize video output.
        """
        # close the window
        hardware.stopVideo()
        
    def logResolution(self):
        """
        Note the resolution and windowedness in the video log.
        """
        # figure out if we're full screen or in a window and set fs to be an appropriate string in a tuple to note the mode in the log message
        if hardware.getFullscreen():
            fs = ("Fullscreen",)
        else:
            fs = ("Window",)

        # log the resolution and mode
        self.logMessage("R\t%d\t%d\t%s" % (self.screensize + fs))
    def toggleFullscreen(self):
        """
        Toggle the fullscreen status of the display.
        """
        # toggle
        hardware.toggleFullscreen()

        # log the resolution again
        self.logResolution()
    def setCaption(self, caption):
        """
        Set window caption.
        """
        # set the caption
        hardware.setCaption(caption)
    def setMaximumFramerate(self, fps = None):
        """
        Set a framerate limit.  None means no limit.

        This can be used to enforce a particular framerate.
        """
        if fps:
            # if fps is provided, calculate and set the minimum frame duration
            self.minframeduration = 1000L / fps
        else:
            # otherwise, set it to zero
            self.minframeduration = 0L
    def getResolution(self):
        """
        Return an x, y tuple of the screen's resolution.
        """
        # return the saved resolution
        return self.screensize
    def clear(self, color = None, keep_background=True):
        """
        Clear basic video.  Make a color background or no background
        in unspecified.
        """
        # clear by unshowing all the pending items
        # get list of pending items
        if color != None or keep_background==False:
            # remove them all
            toclear = [p[0] for p in self.pending]
        else:
            # keep any background color they have set
            toclear = []
            for p in self.pending:
                if not isinstance(p[1], SolidBackground):
                    toclear.append(p[0])
        # unshow what we've selected
        self.unshow(*toclear)

        # if a color is provided we want to show that after we've removed everything else...
        if color != None:
            # create a SolidBackground object
            bg = SolidBackground(Color(color))

            # show the background, returning the shown object
            return self.show(bg, 0, 0)
    def show(self, showable, x, y):
        """
        Draw a basic video element.
        """
        # persistently load the showable
        showable.requireLoaded()
        
        # create a new Shown object to represent this instance of the showable on the screen
        shown = Shown(x,y,*showable.getSize())

        # add the shown, showable, and position to the pending list
        self.pending.append((shown, showable, x, y))

        if isinstance(showable, ActiveShowable):
            # if it's an active showable, increment the activingpending count
            self.activepending += 1
        
        # return the shown
        return shown
    def showProportional(self, showable, x, y, constrain=True):
        """
        showProportional displays a showable, with its position
        specified as a proportion of the width and height of the whole
        screen, such that (0.5,0.5) is the center.

        The original (default) implementation of this was designed so
        that objects would be placed at the edge (but not spilling
        out) of the screen when the proportion was set to 0 or
        1. Leave constrain=True to keep this behavior.

        However, in retrospect, it makes more sense for these
        proportion values to refer to the center of the object, such
        that the object is 50% off the screen when the proportions are
        0 or 1. For this behavior, set constrain=False. See
        http://sourceforge.net/forum/forum.php?thread_id=1871462&forum_id=548620
        for a clear demonstration of these two behaviors.
        
        """
        # get the size of the showable
        objectsize = showable.getSize()

        if constrain:
            # calculate the correct pixel position (for the upper left corner) based on the showable size and the screen size
            position = (int((self.screensize[0] - objectsize[0]) * x), int((self.screensize[1] - objectsize[1]) * y))
        else:
            # center the object at the specified position without the
            # constraint that the object must be fully in the screen
            position = (int((self.screensize[0] * x) - (objectsize[0] / 2)), int((self.screensize[1] * y) - (objectsize[1] / 2))) 
            
        # show the showable at the calculated position, returning the Shown object
        return self.show(showable, *position)
    def showCentered(self, showable):
        """
        """
        # do a showProportional with coordinates (0.5, 0.5)
        return self.showProportional(showable, 0.5, 0.5)
    def showRelative(self, showable, relation, shown, offset = 0):
        """
	Show a showable relative to another shown object.  You can
	optionally specify an offset in the relative direction.
	Relations can be one of BELOW, ABOVE, LEFT, RIGHT, OVER.  The
	offset does not apply to the OVER relation.
        """
        # iterate through the pending list looking for the shown specified...
        for xshown, xshowable, x, y in self.pending:
            # when we find it...
            if xshown is shown:
                # get the size of the associated showable
                xs, ys = xshowable.getSize()

                # get the size of the new showable
                xs2, ys2 = showable.getSize()

                # calculate the pixel position based on the sizes and positions of the showables and which relation is used...
                if relation is BELOW:
                    position = (x + (xs / 2) - (xs2 / 2), y + ys + offset)
                elif relation is ABOVE:
                    position = (x + (xs / 2) - (xs2 / 2), y - ys2 - offset)
                elif relation is LEFT:
                    position = (x - xs2 - offset, y + (ys / 2) - (ys2 / 2))
                elif relation is RIGHT:
                    position = (x + xs + offset, y + (ys / 2) - (ys2 / 2))
                elif relation is OVER:
                    position = (x + (xs / 2) - (xs2 / 2), y + (ys / 2) - (ys2 / 2))
                else:
                    # raise an exception if the relation provided is not recognized
                    raise ValueError, "Invalid positional relation: %r" % relation
                # show the new showable at the calculated position, returning the Shown object
                return self.show(showable, *position)
        # if we never found a matching Shown, raise an exception
        raise ValueError, "Shown not present."
    
    def propToPixel(self, x, y):
	"""
	Convert proportional coordinates to actual pixel values.

	Returns a tuple for the actal position in pixels.
	"""
	return (int(self.screensize[0]*x),int(self.screensize[1]*y))
	
    def showAnchored(self, showable, anchor, relPosition, offset = (0,0), isProp = True):
	"""	
	Place a showable relative to any point on the screen or
	another showable, using anchor points on the showable.  

	FUNCTION:
	  shown = showAnchored(showable,anchor,relPosition, offset=(0,0), isProp=True)

	INPUT ARGS:
	  showable - Showable to place.
	  anchor - Anchor point on the showable (NORTH, SOUTH, EAST, WEST, NORTHWEST, NORTHEAST, SOUTHWEST, SOUTHEAST, CENTER) 
	  relPosition - Screen position in pixels.  You can use propToPixel or a shown object (shown.NorthWest, shown.Center) to specify the pixel position.
	  offset - Offset in pixels or proportional units (see isProp arg) from the relPosition to place the showable by its anchor.
	  isProp - Whether the offset is in pixels or proportional units.

        OUTPUT ARGS:
	  shown - The object that was shown.

	"""
	
	# get the width and height of the showable
	width, height = showable.getSize()

	# see if must convert offset from proportional units
	if isProp:
	    offset = (int(self.screensize[0] * offset[0]), int(self.screensize[1] * offset[1]))

	# adjust the position based on the desired anchor
	if anchor is SOUTHWEST:
	    adjust = (0, -height)
	elif anchor is WEST:
	    adjust = (0, -(height/2))
	elif anchor is NORTHWEST:
	    adjust = (0, 0)
	elif anchor is NORTH:
	    adjust = (-(width/2), 0)
	elif anchor is NORTHEAST:
	    adjust = (-width, 0)
	elif anchor is EAST:
	    adjust = (-width, -(height/2))
	elif anchor is SOUTHEAST:
	    adjust = (-width, -height)
	elif anchor is SOUTH:
	    adjust = (-(width/2), -height)
	elif anchor is CENTER:
	    adjust = (-(width/2), -(height/2))
	else:
	    # raise an exception if the relation provided is not recognized
	    raise ValueError, "Invalid positional relation: %r" % relation

	# calculate the position to add the object based on the offset and adjustment
	position = (relPosition[0]+offset[0]+adjust[0],relPosition[1]+offset[1]+adjust[1])

	# show the showable and return the shown
	return self.show(showable, *position)

    def unshow(self, *showns):
        """
        Remove showables from display.
        """
        # keep a list of the indices of the entries in the pending list to be deleted
        # we don't delete as we find them because changing the size of the list would corrupt the iterater
        deletes = []

        # iterate through the pending list searching for the given Shown...
        for n, (shown, showable, x, y) in enumerate(self.pending):
            # when we find it...
            if shown in showns:
                if isinstance(showable, ActiveShowable):
                    # decrement the active pending count, if the showable is active
                    self.activepending -= 1
                
                # allow showable to be unloaded
                showable.unrequireLoaded()
                
                # append the index to the deletion list
                deletes.append(n)

        # reverse the deletion list so that we delete from later in the list first
        # this way, the indices for the remaining items to be deleted are still correct
        deletes.reverse()

        # iterate through the deletion list...
        for n in deletes:
            # ...deleting as we go
            del self.pending[n]
    def getPosition(self, shown):
        """
        Return the position of the Shown on the screen.
        """
        # iterate through the pending list searching for the shown provided...
        for xshown, showable, x, y in self.pending:
            # when we find it...
            if xshown is shown:
                # ...return its position
                return x, y

        # if we never found it, raise an exception
        raise ValueError, "Shown not present."
    def replace(self, shown, showable):
        """
        Replace a shown object with a new object.
        """
        # iterate through the pending list searching for the shown provided...
        for xshown, xshowable, x, y in self.pending:
            # when we find it...
            if xshown is shown:
                # ...unshow it
                self.unshow(shown)

                # ...and show the new showable at the same coordinates
                return self.show(showable, x, y)

        # if we never found it, raise an exception
        raise ValueError, "Shown not present."
    def updateScreen(self, t = None, force = False):
        """
        Change the screen output to refect all basic video elements
        drawn.  

	If t is a PresentationClock, updateScreen will tare the time to
        represent the time the update occured, which is critical for
        timing events based on actual screen refreshes as opposed to
        times those refreshes were requested.  
	"""
        # update the onscreen list to match the pending list
        self.onscreen = self.pending[:]

        if self.activepending and not force:
            # if we're in activing mode (and not being forced to ignore it), then we're done
            return
	# handle timing
	clock = None
        if t is None:
            # if t is None, use the current time
            t = timing.now()
        elif isinstance(t, exputils.PresentationClock):
            # if t is a PresentationClock, use the time from that clock
            clock = t
            t = t.get()
            
        # calculate the earliest allowable update time, based on the minimum frame duration
        mintime = self.last_updated[0] + self.minframeduration
        
        if t < mintime:
            # if t is before the the earliest allowable time, set t to the earliest allowable time
            t = mintime

        # iterate through the onscreen list...
        for shown, showable, x, y in self.onscreen:
            # ...showing everything in order
            showable.show(x, y)

        # update the screen at the calculated time
	# now passes in self as a video track instance
        #r = hardware.makeVideoChanges(t,self)  
        r = hardware.makeVideoChanges(t)  
        
        for fnc, targs, dargs in self.do_after_update:
            # perform all waiting do_after_update calls
            fnc(*targs, **dargs)

        # ...and clear the do_after_update list
        self.do_after_update = []

        for cb in self.update_callbacks:
            # call all update callbacks
            cb()(r)

        # log the contents of the display
        self.logDisplay(r)

        # save the update timestamp as the time of last update
        self.last_updated = r

	# see if we should tare the time 
	if clock is not None:
	    # we have a clock
            # accumulate errors
            clock.accumulatedTimingError += r[0]-t
            #so tare the clock to the presentation time
	    clock.tare(r)

        # return the timestamp
        return r
    def renderLoop(self, f, *pargs, **kwargs):
        """
        There has to be a render loop when active drawables are
        displayed.
        """
        # mark the start of the render loop in the log
        self.logMessage("ENTERLOOP")
        
        prev_last_updated = self.last_updated
        fpsFrameCount = 1
        fpsMinimumFrames = 50
        fpsText = None
        t_delta = 0.0

        # keep calling f until it returns a false value...
        while f(self.last_updated, *pargs, **kwargs):
            # after each call to f:
            # poll for events
            hardware.pollEvents()

            # calculate the earliest allowable update time, based on the minimum frame duration
            mintime = self.last_updated[0] + self.minframeduration

            # get the current time
            t = timing.now()

            if t < mintime:
                # if the current time is earlier than the earliest allowable time, use the earliest allowable time instead
                t = mintime

            # iterate through the onscreen list...
            for shown, showable, x, y in self.onscreen:
                # ...showing everything in order
                showable.show(x, y)
            
            # Show FPS
            if self.showFPS:
                t1 = prev_last_updated[0]
                t2 = self.last_updated[0]
                t_delta += t2 - t1
                if t_delta and fpsFrameCount >= fpsMinimumFrames:
                    fps = fpsFrameCount * 1000.0 / t_delta
                    fpsText = Text("%.1fFPS"  % fps)
                    fpsFrameCount = 1
                    t_delta = 0.0
                else:
                    fpsFrameCount += 1
                if fpsText:
                    fpsText.show(0, 0)

            # update the screen at the calculated time
            prev_last_updated = self.last_updated
            #self.last_updated = hardware.makeVideoChanges(t, self)
            self.last_updated = hardware.makeVideoChanges(t)

            # log the contents of the display
            self.logDisplay(self.last_updated)

            for cb in self.update_callbacks:
                # call all update callbacks
                cb()(self.last_updated)
            for fnc, targs, dargs in self.do_after_update:
                # perform any waiting do_after_update calls
                fnc(*targs, **dargs)

            # ...and clear the do_after_update list
            self.do_after_update = []

        # mark the end of the render loop in the log
        self.logMessage("EXITLOOP")
    def doAfterUpdate(self, f, *targs, **dargs):
        """
        """
        # append the call to the do_after_update list
        self.do_after_update.append((f, targs, dargs))
    def logDisplay(self, timestamp = None):
        """
        Log the basic video components currently displayed.
        """
        # if we are currently logging...
        if self.logall:
            if timestamp == None:
                # if the timestamp is not given, use the current time
                timestamp = (timing.now(), 0L)

            # get the number of showables on screen
            t = len(self.onscreen)

            # log a header message for this update
            self.logMessage("D\t0/%d\t0\t0\tUPDATE" % t, timestamp)

            for n, (showable, showable, x, y) in enumerate(self.onscreen):
                # log each showable on the screen
                self.logMessage("D\t%d/%d\t%d\t%d\t%s" % (n + 1, t, x, y, showable.logLine()), timestamp)
    def toFront(self, shown):
        """
        """
        # iterate through the pending list searching for the given shown...
        for n, (xshown, showable, x, y) in enumerate(self.pending):
            # when we find it...
            if xshown is shown:
                # remove it from the pending list
                del self.pending[n]

                # ...and append it to the end of the list
                self.pending.append((xshown, showable, x, y))

                # then return
                return
            
        # if we never found a matching Shown, raise an exception
        raise ValueError, "Shown not present."
    def toBack(self, shown):
        """
        """
        # iterate through the pending list searching for the given shown...
        for n, (xshown, showable, x, y) in enumerate(self.pending):
            # when we find it...
            if xshown is shown:
                # remove it from the pending list
                del self.pending[n]

                # ...and insert it at the beginning of the list
                self.pending.insert(0, (xshown, showable, x, y))

                # then return
                return
            
        # if we never found a matching Shown, raise an exception
        raise ValueError, "Shown not present."
    def putBehind(self, shown1, shown2):
        """
        """
        # iterate through the pending list searching for shown2...
        for n2, (shown, showable, x, y) in enumerate(self.pending):
            # when we find it...
            if shown is shown2:
                # go on to the next loop
                break
        else:
            # if we never found a matching Shown, raise an exception
            raise ValueError, "Shown (#2) not present."

        # iterate through the pending list searching for shown1...
        for n1, (shown, showable, x, y) in enumerate(self.pending):
            # when we find it...
            if shown is shown1:
                # remove it from the pending list
                del self.pending[n1]

                # ...and insert it before the position of shown2
                self.pending.insert(n2, (shown1, showable, x, y))

                # then return
                return
        # if we never found a matching Shown, raise an exception
        raise ValueError, "Shown (#1) not present."
    def putInFrontOf(self, shown1, shown2):
        """
        """
        # iterate through the pending list searching for shown2...
        for n2, (shown, showable, x, y) in enumerate(self.pending):
            # when we find it...
            if shown is shown2:
                # go on to the next loop
                break
        else:
            # if we never found a matching Shown, raise an exception
            raise ValueError, "Shown (#2) not present."

        # iterate through the pending list searching for shown1...
        for n1, (shown, showable, x, y) in enumerate(self.pending):
            # when we find it...
            if shown is shown1:
                # remove it from the pending list
                del self.pending[n1]

                # ...and insert it after the position of shown2
                self.pending.insert(n2 + 1, (shown1, showable, x, y))

                # then return
                return
        # if we never found a matching Shown, raise an exception
        raise ValueError, "Shown (#1) not present."
    def addUpdateCallback(self, cb):
        """
        Call cb whenever the screen is updated.
        """
        # append an update callback using a weak reference, so that it cleans itself up
        self.update_callbacks.append(weakref.ref(cb, self.removeUpdateCallback))
    def removeUpdateCallback(self, cbref):
        """
        This method is used to clean up callbacks that no longer
        exist.
        """
        try:
            # try to remove an update callback
            self.update_callbacks.remove(cbref)
        except ValueError:
            # if it fails, it must have cleaned itself up automatically, and that's fine
            pass

    def setGammaRamp(self,red,green,blue):
	"""
	Sets the gamma ramp to correct monitor distortions.  Returns True on success.
	"""
	# Call the set_gamma_ramp function
	return hardware.setGammaRamp(red,green,blue)
    def loadGammaRampFile(self,filename):
	"""
	Load gamma ramp information from a file.  Returns
	red,green,blue lists.  If the file only contains a single
	column, it will be replicated into the other two columns.
	"""
	# Function inspired by VisionEgg function
	fid = open(filename,'r')
	gvals = []
	for line in fid.readlines():
	    # clean up the line
	    line = line.strip()
	    
	    # convert strings to numbers and append
	    gvals.append(map(int,line.split()))
	    
	    # make sure we got three values
	    if len(gvals[-1]) != 3:
		raise ValueError("Expected 3 values per row")

	# make sure we got 256 lines
	if len(gvals) != 256:
	    raise ValueError("Expected 256 rows")
	
	# split out to three rgb
	red, green, blue = zip(*gvals)

	return red,green,blue

    def playMovie(self,movie,t=None,doDelay=True,loops=0):
        """
        Start playback of a movie object.

        INPUT ARGS:
           movie- Instance of a Movie object.
           t- Time or presentation clock instance to control onset time.
           doDelay- Whether to advance the clock the length of the movie.
                    Defaults to True
           loops- Number of times the movie will be repeated. A value of
                  -1 will repeat forever.

        OUTPUT ARGS:
           timestamp- When the first frame played
        """
        # make sure it's not in the playing movies
        if movie in self._playing_movies:
            raise RuntimeError('You can only play a movie instance once.')
        
        # handle timing
	clk = None
        if t is None:
            # if t is None, use the current time
            t = timing.now()
        elif isinstance(t, exputils.PresentationClock):
            # if t is a PresentationClock, use the time from that clock
            clk = t
            t = t.get()

        # are there any movies already playing
        numPlaying = len(self._playing_movies)
        
        (timeInterval, start_timestamp) = timing.timedCall(t,
                                                           self._startMovie,
                                                           movie,loops)
        
        # start the callback if it's not already started
        if numPlaying == 0:
            hardware.addPollCallback(self._playingMovieCallback)

        # log it
        self.logMessage("%s\t%s\t%s" % \
                        ("MOVIE_PLAY",movie.filename,
                         movie.getRemainingTime()), timeInterval)

        # tare the clock to the start time if we have a clock
        if doDelay and clk:
            # accumulate the error
            clk.accumulatedTimingError += start_timestamp[0]-t
            # tare the clock and delay the proper amount.
            # I'm basing this on when the movie.play began, not when
            # the first frame was rendered.
            clk.tare(timeInterval[0])
            clk.delay(movie.getRemainingTime())

        # return the start time
        return start_timestamp

    def _startMovie(self,movie,loops=0):
        # start playing the movie
        movie.play(loops)

        # add it to the playing movies
        self._playing_movies.append(movie)
        
        # call the callback once to get the starting time
        self._playingMovieCallback()
        return self.last_frame_timestamp

    def _playingMovieCallback(self):
        # loop over playing movies to see if we have a new frame
        hasNewFrame = False
        for mov in self._playing_movies:
            if mov.movie.get_busy():
                if mov.hasNewFrame():
                    hasNewFrame = True
            else:
                # we are done with this movie, so remove it from the
                # list and tell it to stop
                self.stopMovie(mov)

        # see if we need to refresh the screen
        if hasNewFrame:
            # see if restart logging
            if self.logall:
                self.logall = False
                restartLogging = True
            else:
                restartLogging = False
            self.last_frame_timestamp = self.updateScreen()
            if restartLogging:
                self.logall = True

    def stopMovie(self,movie,t=None):
        # make sure it was playing
        if movie in self._playing_movies:
            # stop the movie at the specified time
            (timeInterval,res) = timing.timedCall(t,
                                              movie.stop)

            # remove it from the playlist
            # not sure why it's sometimes not there to remove
            try:
                self._playing_movies.remove(movie)
            except:
                print self._playing_movies
                pass
            
            # see if remove callback
            if len(self._playing_movies) == 0:
                # none left to play, so stop callback
                hardware.removePollCallback(self._playingMovieCallback)

            self.logMessage("%s\t%s\t%s" % \
                            ("MOVIE_STOP",movie.filename,
                             movie.getRemainingTime()), timeInterval)

    def stopAllMovies(self):
        for movie in self._playing_movies:
            # stop the movie
            (timeInterval,res) = timing.timedCall(0,
                                              movie.stop)

            # remove it from the playlist
            self._playing_movies.remove(movie)

            # see if remove callback
            if len(self._playing_movies) == 0:
                # none left to play, so stop callback
                hardware.removePollCallback(self._playingMovieCallback)

            self.logMessage("%s\t%s\t%s" % \
                            ("MOVIE_STOP",movie.filename,
                             movie.getRemainingTime()), timeInterval)

        
    def pauseMovie(self,movie,t=None):
        # make sure it was playing
        if movie in self._playing_movies:
            # pause the movie
            (timeInterval,res) = timing.timedCall(t,
                                              movie.pause)

            # remove it from the playlist
            self._playing_movies.remove(movie)

            # see if remove callback
            if len(self._playing_movies) == 0:
                # none left to play, so stop callback
                hardware.removePollCallback(self._playingMovieCallback)

            self.logMessage("%s\t%s\t%s" % \
                            ("MOVIE_PAUSE",movie.filename,
                             movie.getRemainingTime()), timeInterval)
