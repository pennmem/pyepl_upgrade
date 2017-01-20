# PyEPL: hardware/graphics/__init__.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides 2D graphics functionality.
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
import os

import time

import pyepl
import pyepl.hardware.eventpoll
import pyepl.hardware.timing
from image import LowImage
from font import LowFont
import screensync

pyepldir = os.path.abspath(os.path.dirname(pyepl.__file__))

def initialize(**options):
    """
    Do anything that needs to happen before 2D graphics output can
    happen.
    """
    global init_options
    init_options = options

    # see if set the linux screen sync
    platform = os.uname()[0]
    if platform =='Linux': 
	screensync.linuxSetRefreshBlock(init_options["sync_to_vbl"])

    # init the pygame display
    pygame.display.init()
    pygame.font.init()

def finalize():
    """
    Clean up.
    """
    pygame.display.quit()
    pygame.font.quit()

def toggleFullscreen():
    """
    """
    global fullscreen
    fullscreen = not fullscreen
    pygame.display.toggle_fullscreen()

def getFullscreen():
    """
    """
    global fullscreen
    return fullscreen

def getShowFPS():
    """
    """
    global init_options
    return init_options["show_fps"]

def getResolution():
    """
    Return a 2-tuple of the X, Y resolution of the window.
    """
    return pygame.display.get_surface().get_size()

def setVideoCaption(caption):
    """
    Set the window caption.
    """
    pygame.display.set_caption(caption)

lastclearcolor = None
lastclearimage = None
def clearScreen(color):
    """
    Set the whole window to RGB 3-tuple color.
    """
    global lastclearcolor
    global lastclearimage
    try:
        alpha = color[3]
    except IndexError:
        alpha = 255
    if alpha == 255:
        glClearColor(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, alpha / 255.0)
        glClear(GL_COLOR_BUFFER_BIT)
    else:
        if lastclearcolor != color:
            x, y = pygame.display.get_surface().get_size()
            lastclearimage = LowImage(x + 1, y + 1)
            lastclearimage.fill(color[0], color[1], color[2], alpha)
            lastclearcolor = color
        lastclearimage.show(0, 0)

# thresh is set to 250 microseconds because tests have shown that a
# non-blocking flip takes less than that.  It will be necessary to
# test this more.  Keep in mind that if it does block, but takes less
# than 250us, then we will essentially miss a frame, reporting that
# the image came on the screen one frame after it actually did.
blockThresh = .000250

# max number of flips to prevent loop.  If we don't block after 5,
# then something is wrong.
maxFlips = 5
def doMultiFlips(vTrack):
    """
    In order to block correctly, we must call a second flip if the
    first flip did not block.  The only issue is that we have to copy
    the front buffer to the back buffer before we call flip again.

    It passes in the instance of the video track so that it can redraw
    the pending showables on the back buffer to enable multiple flips.
    """
    # get thresh for if blocking
    global blockThresh
    global maxFlips

    # time the first flip
    starttime = time.time() #pyepl.hardware.timing.universal_time()
    pygame.display.flip()
    endtime = time.time() #pyepl.hardware.timing.universal_time()
    
    # see if the flip took no time
    if endtime - starttime < blockThresh:
	# Must call the flip again
	# copy front buffer to back

	# get the screen size
	#w, h = pygame.display.get_surface().get_size()
        
	# draw everything to back buffer
	# iterate through the onscreen pending list...
        for shown, showable, x, y in vTrack.pending:
            # ...showing everything in order
            showable.show(x, y)
	
	# flip until blocked
	starttime = time.time()
	pygame.display.flip()
	endtime = time.time()
	count = 0
	while (endtime-starttime)<blockThresh and count < maxFlips:	    
	    starttime = time.time()
	    pygame.display.flip()
	    endtime = time.time()
	    count = count + 1

#     # uncomment the following few lines for debugging
# 	print count+1, (endtime-starttime)*1000.
#     else:
# 	print 0, (endtime-starttime)*1000.

	#############
	# the old slow way
	# perform the opengl buffer copy
	#glReadBuffer (GL_FRONT)
	#glDrawBuffer (GL_BACK)
	#glCopyPixels (0,0,w,h,GL_COLOR)
	
	# call flip
	#pygame.display.flip()
	#############

def doBlockingFlip():
    """
    Perform a flip and then write a pixel to the back buffer to pause
    the pipeline.  Inspired by PsychToolbox code.
    """

    # do the flip
    pygame.display.flip()
    
    # The following is taken from the PsychToolbox
    # Draw a single pixel in left-top area of back-buffer. This will wait/stall the rendering pipeline
    # until the buffer flip has happened, aka immediately after the VBL has started.
    # We need the pixel as "synchronization token", so the following glFinish() really
    # waits for VBL instead of just "falling through" due to the asynchronous nature of
    # OpenGL:
    glDrawBuffer(GL_BACK)
    # We draw our single pixel with an alpha-value of zero - so effectively it doesn't
    # change the color buffer - just the z-buffer if z-writes are enabled...
    glColor4f(0,0,0,0)
    glBegin(GL_POINTS)
    glVertex2i(10,10)
    glEnd()
    # This glFinish() will wait until point drawing is finished, ergo backbuffer was ready
    # for drawing, ergo buffer swap in sync with start of VBL has happened.
    glFinish()

# vTrack has to be optional because the clock is currently optional.
#def makeVideoChanges(t = None, vTrack=None):
def makeVideoChanges(t = None):
    """
    At time t, update the screen to reflect all prior changes.
    Returns a timestamp indicating when the update actually happened.
    """
    # See if syncing or not
    if init_options["sync_to_vbl"]:
	# Call the multiple flip saving the timestamp
	#tempstamp = pyepl.hardware.timing.timedCall(t, doMultiFlips, vTrack)[0]
	tempstamp = pyepl.hardware.timing.timedCall(t, doBlockingFlip)[0]
	# return adjusted time based on the blocking
        timestamp = (tempstamp[0]+tempstamp[1]-1,1)
        # timestamp = tempstamp  # for debugging to see latencies
    else:
	# Just call single flip
	timestamp = pyepl.hardware.timing.timedCall(t, pygame.display.flip)[0]

    return timestamp

def startVideo():
    """
    """
    global init_options
    global fullscreen
    flags = DOUBLEBUF
    flags |= OPENGL
    # check fullscreen setting:
    fullscreen = init_options["fullscreen"]
    if fullscreen:
        flags |= FULLSCREEN
    platform = os.uname()[0]
    if platform == 'Darwin':
	pygame.display.set_mode(init_options["resolution"], flags, 24)
	# on the mac, we set up VBL syncing after opengl init...
	# check VBL-sync setting:
	if init_options["sync_to_vbl"]:
	    # sync to the VBL
	    screensync.setRefreshBlock()
    if platform == 'Linux':
	pygame.display.set_mode(init_options["resolution"], flags)
    
    pygame.display.set_caption("PyEPL VideoTrack")
    
    # hide the mouse pointer
    pygame.mouse.set_visible(False)
    
    # set the icon and the splash image
    pygame.display.set_icon(pygame.image.load(os.path.join(pyepldir, "resources", "icon.png")))
    x, y = init_options["resolution"]
    LowImage(os.path.join(pyepldir, "resources", "splash.png")).scale(x + 1, y + 1).show(0, 0)
    pygame.display.flip()

def stopVideo():
    """
    """
    pass

def setGammaRamp(red,green,blue):
    """
    """
    # Call the set_gamma_ramp function
    return pygame.display.set_gamma_ramp(red,green,blue)
    
