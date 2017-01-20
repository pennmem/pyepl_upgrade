# PyEPL: vr/__init__.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This package provides the virtual reality features of PyEPL.
"""

import pyepl.hardware.vr
import pyepl.display
from pyepl.display import ActiveShowable
from pyepl.textlog import LogTrack
import pyepl.mechinput
import weakref
import randomposition
import geometry

class NoSkyboxImageError(Exception):
    pass

class VEye(ActiveShowable):
    """
    A VEye represents a virtual camera.  It can be controlled
    independently, or attached to an avatar.
    """
    def __init__(self, eye, name, track, avatar = None):
        """
        Construct a VEye object from a LowVEye (low-level
        implementation), a name, a VRTrack, and possibily an avatar to
        which the eye is attached.
        """
        ActiveShowable.__init__(self)
        self.eye = eye
        self.name = name
        self.track = track
        self.avatar = avatar
        if avatar:
            self.lookat = None
        else:
            self.lookat = (self.name, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    def reposition(self, x, y, z, yaw, pitch, roll):
        """
        Position the camera.
        """
        self.eye.reposition(x, y, z, yaw, pitch, roll)
        self.lookat = (self.name, pos[0], pos[1], pos[2], target[0], target[1], target[2], up[0], up[1], up[2], None)
    def setFOV(self, fov):
        """
        Set the field of view, in radians, without moving the camera.
        """
        self.eye.setFOV(fov)
        self.lookat = (self.name, 0, 0, 0, 0, 0, 0, 0, 0, 0, fov)
    def show(self, x, y):
        """
        Render the scene to the screen.
        """
        if self.avatar:
            self.avatar.drawNotify(self)
        self.eye.draw(x, y)
        if self.lookat:
            self.track.eyeLookAtLog(*self.lookat)
            self.lookat = None
    def getSize(self):
        """
        """
        return self.eye.getSize()
    def logLine(self):
        """
        Uniquely represent this object for the display log.
        """
        return "VEYE\t%s\t%d\t%d" % ((self.name,) + self.eye.getSize())

class VAvatar:
    """
    A VAvatar object represents a user's position, orientation, and
    body shape in the virtual environment.
    """
    def __init__(self, avatar, name, track):
        """
        Construct a VAvatar from a LowVAvatar (low-level
        implementation), a name, and a VRTrack.
        """
        self.avatar = avatar
        self.name = name
        self.track = track
        self.eyes = []
        self.controls = {}
    def newEye(self, name, xsize = None, ysize = None):
        """
        Create a VEye attached to this avatar with the dimensions
        provided.
        """
        if xsize == None or ysize == None:
            xsize, ysize = self.track.videotrack.getResolution()
        eye = VEye(pyepl.hardware.vr.LowVEye(self.track.env, xsize, ysize), name, self.track, self)
        self.avatar.attachEye(eye.eye)
        self.track.eyeAttachLog(name, self.name)
        self.eyes.append(weakref.ref(eye, self.expireEye))
        return eye
    def expireEye(self, eyeref):
        """
        This fuction is used for housekeeping when an attached eye is
        destroyed.
        """
        if eyeref():
            self.avatar.dettachEye(eyeref().eye)  # will this ever happen? :-(
            self.eyes.remove(eyeref)
    def drawNotify(self, eye):
        """
        When one of our attached eyes is about to render itself to the
        screen, we want to know so that we can make sure that the
        camera positions are up-to-date.
        """
        if eye == self.eyes[0]():
            self.avatar.travel(**dict(map(lambda item: (item[0], item[1].getPosition()), self.controls.iteritems())))
            self.track.avatarMoveLog(self.name, *self.avatar.positionOrientation())
    def positionOrientation(self):
        """
        """
        return self.avatar.positionOrientation()
    def setControls(self, **controls):
        """
        Set mechanical input abstraction objects to control this
        avatar's movement.
        """
        self.controls = controls

class VRTrack(LogTrack):
    """
    This class is the starting point for access to all VR features.
    It can keep a log of all VR activity.
    """
    logExtension = ".vrlog"
    def __init__(self, basename, archive = None, autoStart = True):
        """
        Create the VRTrack.
        """
        self.env = None
        LogTrack.__init__(self, basename, archive, autoStart)
        self.archive = archive
        self.logqueue = []
    def startService(self):
        self.videotrack = pyepl.display.VideoTrack.lastInstance()
        self.cb = self.markScreenUpdate
        self.videotrack.addUpdateCallback(self.cb)
        self.env = pyepl.hardware.vr.LowVEnvironment()
    def stopService(self):
        try:
            self.videotrack.removeUpdateCallback(self.cb)
        except AttributeError:
            pass
        self.env = None
    def resetEnvironment(self):
        """
        """
        self.logMessage("RESET")
	self.env.__del__()
        self.env = pyepl.hardware.vr.LowVEnvironment()
    def newEye(self, name, xsize = None, ysize = None):
        """
        Create a VEye for the loaded environment.
        """
        if xsize == None or ysize == None:
            xsize, ysize = track.videotrack.getResolution()
        return VEye(pyepl.hardware.vr.LowVEye(self.env, xsize, ysize), name, self)
    def newAvatar(self, name, *targs, **dargs):
        """
        Create a VAvatar for the loaded environment.
        """
        return VAvatar(pyepl.hardware.vr.LowVAvatarSpeedBubble(self.env, *targs, **dargs), name, self)
    def addSphereGeom(self, x, y, z, radius, **surf):
        """
        """
        r = self.env.addEntity(pyepl.hardware.vr.SphereGeom(x, y, z, radius, **surf))
        self.logMessage("I\tSPHEREGEOM\t%s\t%s\t%d" % ((x, y, z, radius), repr(surf), id(r)))
        return r
    def addBoxGeom(self, x, y, z, xsize, ysize, zsize, **surf):
        """
        """
        r = self.env.addEntity(pyepl.hardware.vr.BoxGeom(x, y, z, xsize, ysize, zsize, **surf))
        self.logMessage("I\tBOXGEOM\t%s\t%s\t%d" % ((x, y, z, xsize, ysize, zsize), repr(surf), id(r)))
        return r
    def addPlaneGeom(self, a, b, c, d, **surf):
        """
        """
        r = self.env.addEntity(pyepl.hardware.vr.PlaneGeom(a, b, c, d, **surf))
        self.logMessage("I\tPLANEGEOM\t%s\t%s\t%d" % ((a, b, c, d), repr(surf), id(r)))
        return r
    def addBuildingBox(self, x, y, z, image, width, height, roofimage = None, rooftexlen = None, texlen = None):
        """
        """
        if roofimage:
            roofimg = roofimage.getLowUnscaled()
            rfn = roofimage.filename
        else:
            rfn = None
            roofimg = None
        r = self.env.addEntity(pyepl.hardware.vr.BuildingBox(x, y, z, image.getLowUnscaled(), width, height, roofimg, rooftexlen, texlen))
        self.logMessage("I\tBUILDINGBOX\t%s\t%d" % ((x, y, z, image.filename, width, height, rfn, rooftexlen, texlen), id(r)))
        return r
    def addSphere(self, x, y, z, image, radius, slices = 16, stacks = 16):
        """
        """
        r = self.env.addEntity(pyepl.hardware.vr.Sphere(x, y, z, image.getLowUnscaled(), radius, slices, stacks))  #inefficient for sky!
        self.logMessage("I\tSPHERE\t%s\t%d" % ((x, y, z, image.filename, radius, slices, stacks), id(r)))
        return r
    def addFloorBox(self, x, y, z, xsize, ysize, zsize, floorimage, floortexlen = None, wallimage = None, walltexlen = None, wallFrontImage = None, wallFrontTexlen = None, wallRearImage = None, wallRearTexlen = None, wallLeftImage = None, wallLeftTexlen = None, wallRightImage = None, wallRightTexlen = None):
        if wallimage:
            wallimgFront = wallimage.getLowUnscaled()
            wFrontFn = wallimage.filename
            wallimgRear = wallimage.getLowUnscaled()
            wRearFn = wallimage.filename
            wallimgLeft = wallimage.getLowUnscaled()
            wLeftFn = wallimage.filename
            wallimgRight = wallimage.getLowUnscaled()
            wRightFn = wallimage.filename
            wtxlnFront = walltexlen
            wtxlnRear = walltexlen
            wtxlnLeft = walltexlen
            wtxlnRight = walltexlen
        else:
            wallimgFront = None
            wFrontFn = None
            wallimgRear = None
            wRearFn = None
            wallimgLeft = None
            wLeftFn = None
            wallimgRight = None
            wRightFn = None
            wtxlnFront = walltexlen
            wtxlnRear = walltexlen
            wtxlnLeft = walltexlen
            wtxlnRight = walltexlen
        if wallFrontImage:
            wallimgFront = wallFrontImage.getLowUnscaled()
            wFrontFn = wallFrontImage.filename
            wtxlnFront = wallFrontTexlen
        if wallRearImage:
            wallimgRear = wallRearImage.getLowUnscaled()
            wRearFn = wallRearImage.filename
            wtxlnRear = wallRearTexlen
        if wallLeftImage:
            wallimgLeft = wallLeftImage.getLowUnscaled()
            wLeftFn = wallLeftImage.filename
            wtxlnLeft = wallLeftTexlen
        if wallRightImage:
            wallimgRight = wallRightImage.getLowUnscaled()
            wRightFn = wallRightImage.filename
            wtxlnRight = wallRightTexlen
            
        r = self.env.addEntity(pyepl.hardware.vr.FloorBox(x, y, z, xsize, ysize, zsize, floorimage.getLowUnscaled(), floortexlen, wallimgFront, wtxlnFront, wallimgRear, wtxlnRear, wallimgLeft, wtxlnLeft, wallimgRight, wtxlnRight))
        self.logMessage("I\tFLOORBOX\t%s\t%d" % ((x, y, z, xsize, ysize, zsize, floorimage.filename, floortexlen, wFrontFn, wtxlnFront, wRearFn, wtxlnRear, wLeftFn, wtxlnLeft, wRightFn, wtxlnRight), id(r)))
        return r
    def addSkyBox(self, image=None, imageFront=None, imageRear=None, imageLeft=None, imageRight=None, x = 0.0, y = 0.0, z = 0.0, xsize = 500.0, ysize = 500.0, zsize = 500.0, texlen = 500.0, texlenFront = 500.0, texlenRear = 500.0, texlenLeft = 500.0, texlenRight = 500.0, xTileFactorFront = 1, xTileFactorRear = 1, xTileFactorLeft = 1, xTileFactorRight = 1, yTileFactorFront = 1, yTileFactorRear = 1, yTileFactorLeft = 1, yTileFactorRight = 1):
        if image:
            imgFront = image.getLowUnscaled()
            imgRear = image.getLowUnscaled()
            imgLeft = image.getLowUnscaled()
            imgRight = image.getLowUnscaled()
            txlnFront = texlen
            txlnRear = texlen
            txlnLeft = texlen
            txlnRight = texlen
            imgFrontFn = image.filename
            imgRearFn = image.filename
            imgLeftFn = image.filename
            imgRightFn = image.filename
            
        if imageFront:
            imgFront = imageFront.getLowUnscaled()
            txlnFront = texlenFront
            imgFrontFn = imageFront.filename           
        if imageRear:
            imgRear = imageRear.getLowUnscaled()
            txlnRear = texlenRear
            imgRearFn = imageFront.filename
        if imageLeft:
            imgLeft = imageLeft.getLowUnscaled()
            txlnLeft = texlenLeft
            imgLeftFn = imageLeft.filename
        if imageRight:
            imgRight = imageRight.getLowUnscaled()
            txlnRight = texlenRight
            imgRightFn = imageRight.filename
            
        if not image and not (imageFront and imageRear and imageLeft and imageRight):
            raise NoSkyBoxImageError()
        
        r = self.env.addEntity(pyepl.hardware.vr.SkyBox(imgFront,imgRear,imgLeft,imgRight, x, y, z, xsize, ysize, zsize, txlnFront, txlnRear, txlnLeft, txlnRight, xTileFactorFront, xTileFactorRear, xTileFactorLeft, xTileFactorRight, yTileFactorFront, yTileFactorRear, yTileFactorLeft, yTileFactorRight))
        self.logMessage("I\tSKYBOX\t%s\t%d" % ((x, y, z, xsize, ysize, zsize, imgFrontFn, txlnFront, imgRearFn, txlnRear, imgLeftFn, txlnLeft, imgRightFn, txlnRight, xTileFactorFront, xTileFactorRear, xTileFactorLeft, xTileFactorRight, yTileFactorFront, yTileFactorRear, yTileFactorLeft, yTileFactorRight), id(r)))
        return r
    def addSprite(self, x, y, z, image, xsize, ysize):
        """
        """
        r = self.env.addEntity(pyepl.hardware.vr.Sprite(x, y, z, image.getLowUnscaled(), xsize, ysize))
        self.logMessage("I\tSPRITE\t%s\t%d" % ((x, y, z, image.filename, xsize, ysize), id(r)))
        return r
    def setGravity(self, x, y, z):
        """
        """
        self.env.setGravity(x, y, z)
        self.logMessage("G\t%f\t%f\t%f" % (x, y, z))
    def setFog(self, mode = None, color = (0.5, 0.5, 0.5), far = 1.0, near = 0.0, density = 1.0):
        """
        """
        self.env.setFog(mode, color, far, near, density)
        self.logMessage("F\t%s\t%r\t%f\t%f\t%f" % (mode, color, far, near, density))
    def removeEntity(self, *entities):
        """
        """
        for entity in entities:
            self.env.removeEntity(entity)
            self.logMessage("D\t%d" % id(entity))
    def markScreenUpdate(self, timestamp):
        """
        We want to know when the screen is actually updated so that
        our log entries have correct timestamps.
        """
        if self.logall:
            for m in self.logqueue:
                self.logMessage(m, timestamp)
        self.logqueue = []
    def eyeLookAtLog(self, eyename, px, py, pz, tx, ty, tz, ux, uy, uz, fov):
        """
        Log a "look at" eye positioning event.
        """
        self.logqueue.append("L\t%s\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f" % (eyename, px, py, pz, tx, ty, tz, ux, uy, uz, fov))
    def eyeAttachLog(self, eyename, avatarname):
        """
        Log the attachment of an eye to an avatar.
        """
        self.logqueue.append("A\t%s\t%s" % (eyename, avatarname))
    def avatarMoveLog(self, avatarname, x, y, z, yaw, pitch, roll):
        """
        Log the movement of an avatar.
        """
        self.logqueue.append("M\t%s\t%f\t%f\t%f\t%f\t%f\t%f" % (avatarname, x, y, z, yaw, pitch, roll))
