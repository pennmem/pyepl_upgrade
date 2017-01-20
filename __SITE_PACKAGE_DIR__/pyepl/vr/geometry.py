# PyEPL: vr/geometry.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
"""

import math

class Vector:
    """
    """
    def __init__(self, x, y, z):
        """
        """
        self.x = x
        self.y = y
        self.z = z
    def __getitem__(self, index):
        """
        """
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        if index == 2:
            return self.z
        raise IndexError, "Vector objects can only be indexed with 0, 1, or 2."
    def length(self):
        """
        """
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
    def __add__(self, other):
        """
        """
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
    def __sub__(self, other):
        """
        """
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
    def __mul__(self, other):
        """
        """
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.x + self.z * other.z
        return Vector(self.x * other, self.y * other, self.z * other)
    def __neg__(self):
        """
        """
        return Vector(-self.x, -self.y, -self.z)
    def __pos__(self):
        """
        """
        return self

class VRWorld:
    """
    """
    def __init__(self):
        """
        """
        self.ambient = (0.6, 0.6, 0.6)
        self.startsector = None
        self.startpos = None
        self.sectors = []
    def getXML(self):
        """
        """
        if self.startsector:
            start = """<start><sector>%s</sector><position x="%s" y="%s" z="%s" /></start>""" % (self.startsector.name, self.startpos[0], self.startpos[1], self.startpos[2])
        else:
            start = ""
        settings = """<ambient red="%s" green="%s" blue="%s" />""" % self.ambient
        p = {}
        m = {}
        for x in self.sectors:
            p.update(x.getPlugins())
            m.update(x.getFactories())
        plugins = "".join(map(lambda plug: """<plugin name="%s">%s</plugin>""" % plug, p.iteritems()))
        meshfacts = "".join(map(lambda mf: """<meshfact name="%s">%s</meshfact>""" % mf, m.iteritems()))
        sects = "".join(map(lambda s: s.getXMLBody(), self.sectors))
        return """<world><settings>%s</settings><plugins>%s</plugins>%s%s<renderpriorities><priority name="sky"><level>1</level><sort>NONE</sort></priority><priority name="wall"><level>2</level><sort>NONE</sort></priority><priority name="object"><level>3</level><sort>BACK2FRONT</sort></priority><priority name="alpha"><level>4</level><sort>BACK2FRONT</sort></priority></renderpriorities>%s</world>""" % (settings, plugins, start, meshfacts, sects)
    def setAmbientColor(self, r, g, b):
        """
        """
        self.ambient = (r, g, b)
    def setStartingPosition(self, sector, position):
        """
        """
        self.startsector = sector
        self.startpos = position
    def newSector(self, name = "room"):
        """
        """
        sector = Sector(name)
        self.sectors.append(sector)
        return sector
    
class Sector:
    """
    """
    def __init__(self, name):
        """
        """
        self.name = name
        self.elements = []
    def getXMLBody(self):
        """
        """
        return """<sector name="%s">%s</sector>""" % (self.name, "".join(map(lambda x: x.getXMLBody(), self.elements)))
    def getPlugins(self):
        """
        """
        p = {}
        for x in self.elements:
            p.update(x.getPlugins())
        return p
    def getFactories(self):
        """
        """
        f = {}
        for x in self.elements:
            f.update(x.getFactories())
        return f
    def addSky(self, image, radius = 100):
        """
        """
        sky = Sky(image, radius)
        self.elements.append(sky)
        return sky
    def addMesh(self, name):
        """
        """
        mesh = Mesh(name)
        self.elements.append(mesh)
        return mesh
    def addFloorBox(self, floorimage, xsize, ysize, wallimage, wallheight, floortexlen = 6):
        """
        """
        floorbox = FloorBox(floorimage, xsize, ysize, wallimage, wallheight, floortexlen)
        self.elements.append(floorbox)
        return floorbox
    def addSimpleBuildingBox(self, name, image, width, height, position, roofimage = None, rooftexlen = 6.0):
        """
        """
        bb = SimpleBuildingBox(name, image, width, height, position, roofimage, rooftexlen)
        self.elements.append(bb)
        return bb
    def addSimpleSprite(self, name, image, width, height, position):
        """
        """
        sprite = SimpleSprite(name, image, width, height, position)
        self.elements.append(sprite)
        return sprite

class Sky:
    """
    """
    def __init__(self, image, radius):
        """
        """
        self.radius = radius
        self.imagepath = image.filename[1:]
    def getXMLBody(self):
        """
        """
        return """<meshobj name="skydome"><plugin>ball</plugin><params><factory>skydome</factory><radius x="%s" y="%s" z="%s" /><numrim>12</numrim><toponly>yes</toponly><reversed>yes</reversed><material>%s</material><lighting>no</lighting><color red="1" green="1" blue="1" /></params><znone /><priority>sky</priority><camera /></meshobj>""" % (self.radius, self.radius, self.radius, self.imagepath)
    def getPlugins(self):
        """
        """
        return {"ball": "crystalspace.mesh.loader.ball", "ballFact": "crystalspace.mesh.loader.factory.ball"}
    def getFactories(self):
        """
        """
        return {"skydome": "<plugin>ballFact</plugin><params />"}

class Mesh:
    """
    """
    def __init__(self, name, priority = "object"):
        """
        """
        self.name = name
        self.priority = priority
        self.verteces = []
        self.polygons = []
        self.current_texture = None
        self.current_texlen = 6.0
    def getXMLBody(self):
        """
        """
        verts = "".join(map(lambda v: """<v x="%s" y="%s" z="%s" />""" % (v[0], v[1], v[2]), self.verteces))
        texture = None
        texlen = None
        polys = []
        for name, points, desired_texture, desired_texlen, options in self.polygons:
            if texture != desired_texture:
                texturemod = """<material>%s</material>""" % desired_texture
                texture = desired_texture
            if texlen != desired_texlen:
                texlenmod = """<texlen>%s</texlen>""" % desired_texlen
                texlen = desired_texlen
            opts = []
            if options.has_key("orig"):
                opts.append("""<orig x="%s" y="%s" z="%s" />""" % options["orig"])
            if options.has_key("first"):
                opts.append("""<first x="%s" y="%s" z="%s" />""" % options["first"])
            if options.has_key("second"):
                opts.append("""<second x="%s" y="%s" z="%s" />""" % options["second"])
            if options.has_key("firstlen"):
                opts.append("""<firstlen>%s</firstlen>""" % options["firstlen"])
            if options.has_key("secondlen"):
                opts.append("""<secondlen>%s</secondlen>""" % options["secondlen"])
            if len(opts):
                texmap = """<texmap>%s</texmap>""" % "".join(opts)
            else:
                texmap = ""
            points = "".join(map(lambda p: """<v>%s</v>""" % p, points))
            polys.append("""%s%s<p name="%s">%s%s</p>""" % (texturemod, texlenmod, name, texmap, points))
        polys = "".join(polys)
        return """<meshobj name="%s"><zfill /><plugin>thing</plugin><params>%s%s</params><priority>%s</priority></meshobj>""" % (self.name, verts, polys, self.priority)
    def getPlugins(self):
        """
        """
        return {"thing": "crystalspace.mesh.loader.thing"}
    def getFactories(self):
        """
        """
        return {}
    def vertex(self, x, y, z):
        """
        """
        r = len(self.verteces)
        self.verteces.append((x, y, z))
        return r
    def setTexture(self, image = None, texlen = None):
        """
        """
        if image:
            self.current_texture = image.filename[1:]
        if texlen:
            self.current_texlen = texlen
    def addPolygon(self, name, *verteces, **options):
        """
        """
        self.polygons.append((name, verteces, self.current_texture, self.current_texlen, options))
    def merge(self, other):
        """
        """
        vertshift = len(self.verteces)
        self.verteces.extend(other.verteces)
        for name, verteces, self.current_texture, self.current_texlen, options in other.polygons:
            self.polygons.append((name, map(lambda x: x + vertshift, verteces), self.current_texture, self.current_texlen, options))

class FloorBox(Mesh):
    """
    """
    def __init__(self, floorimage, xsize, zsize, wallimage, wallheight, floortexlen):
        """
        """
        Mesh.__init__(self, "floorbox", priority = "wall")
        halfx = xsize * 0.5
        halfz = zsize * 0.5
        floorlowerleft = self.vertex(-halfx, 0, -halfz)
        floorlowerright = self.vertex(-halfx, 0, halfz)
        floorupperright = self.vertex(halfx, 0, halfz)
        floorupperleft = self.vertex(halfx, 0, -halfz)
        rooflowerleft = self.vertex(-halfx, wallheight, -halfz)
        rooflowerright = self.vertex(-halfx, wallheight, halfz)
        roofupperright = self.vertex(halfx, wallheight, halfz)
        roofupperleft = self.vertex(halfx, wallheight, -halfz)
        self.setTexture(wallimage, texlen = wallheight)
        self.addPolygon("front", floorupperleft, floorupperright, roofupperright, roofupperleft)
        self.addPolygon("left", floorlowerleft, floorupperleft, roofupperleft, rooflowerleft)
        self.addPolygon("rear", floorlowerright, floorlowerleft, rooflowerleft, rooflowerright)
        self.addPolygon("right", floorupperright, floorlowerright, rooflowerright, roofupperright)
        self.setTexture(floorimage, texlen = floortexlen)
        self.addPolygon("floor", floorlowerleft, floorlowerright, floorupperright, floorupperleft)

class SimpleBuildingBox(Mesh):
    """
    """
    def __init__(self, name, image, width, height, position, roofimage = None, rooftexlen = 6.0, tilewalls = False):
        """
        """
        Mesh.__init__(self, name)
        halfwidth = width * 0.5
        highx = position[0] + halfwidth
        highz = position[2] + halfwidth
        lowx = position[0] - halfwidth
        lowz = position[2] - halfwidth
        lowy = position[1]
        highy = position[1] + height
        floorlowerleft = self.vertex(lowx, lowy, lowz)
        floorlowerright = self.vertex(lowx, lowy, highz)
        floorupperright = self.vertex(highx, lowy, highz)
        floorupperleft = self.vertex(highx, lowy, lowz)
        rooflowerleft = self.vertex(lowx, highy, lowz)
        rooflowerright = self.vertex(lowx, highy, highz)
        roofupperright = self.vertex(highx, highy, highz)
        roofupperleft = self.vertex(highx, highy, lowz)
        self.setTexture(image)
        if tilewalls:
            self.addPolygon("front", floorupperright, floorupperleft, roofupperleft, roofupperright)
            self.addPolygon("left", rooflowerleft, roofupperleft, floorupperleft, floorlowerleft)
            self.addPolygon("rear", rooflowerright, rooflowerleft, floorlowerleft, floorlowerright)
            self.addPolygon("right", roofupperright, rooflowerright, floorlowerright, floorupperright)
        else:
            self.addPolygon("front", floorupperright, floorupperleft, roofupperleft, roofupperright,
                            orig = (highx, highy, highz), first = (highx, highy, lowz), second = (highx, lowy, highz),
                            firstlen = -width, secondlen = height)
            self.addPolygon("left", rooflowerleft, roofupperleft, floorupperleft, floorlowerleft,
                            orig = (highx, highy, lowz), first = (lowx, highy, lowz), second = (highx, lowy, lowz),
                            firstlen = -width, secondlen = height)
            self.addPolygon("rear", rooflowerright, rooflowerleft, floorlowerleft, floorlowerright,
                            orig = (lowx, highy, lowz), first = (lowx, highy, highz), second = (lowx, lowy, lowz),
                            firstlen = -width, secondlen = height)
            self.addPolygon("right", roofupperright, rooflowerright, floorlowerright, floorupperright,
                            orig = (lowx, highy, highz), first = (highx, highy, highz), second = (lowx, lowy, highz),
                            firstlen = -width, secondlen = height)
        if roofimage:
            self.setTexture(roofimage, texlen = rooftexlen)
            self.addPolygon("roof", rooflowerleft, rooflowerright, roofupperright, roofupperleft)

class SimpleSprite:
    """
    """
    def __init__(self, name, image, width, height, position):
        """
        """
        self.name = name
        self.imagepath = image.filename[1:]
        self.width = width
        self.height = height
        self.position = position
    def getXMLBody(self):
        """
        """
        halfwidth = self.width * 0.5
        return """<meshobj name="%s"><zfill /><plugin>sprite</plugin><params><factory>spriteMeshFact</factory><material>%s</material><lighting>no</lighting><v x="%s" y="%s" /><v x="%s" y="%s" /><v x="%s" y="0" /><v x="%s" y="0" /><uv u="0" v="0" /><uv u="1" v="0" /><uv u="1" v="1" /><uv u="0" v="1" /><color red="1" green="1" blue="1" /><color red="1" green="1" blue="1" /><color red="1" green="1" blue="1" /><color red="1" green="1" blue="1" /></params><move><v x="%s" y="%s" z="%s" /></move><priority>object</priority></meshobj>""" % (self.name, self.imagepath, -halfwidth, self.height, halfwidth, self.height, halfwidth, -halfwidth, self.position[0], self.position[1], self.position[2])
    def getPlugins(self):
        """
        """
        return {"sprite": "crystalspace.mesh.loader.sprite.2d", "spriteFact": "crystalspace.mesh.loader.factory.sprite.2d"}
    def getFactories(self):
        """
        """
        return {"spriteMeshFact": "<plugin>spriteFact</plugin><params />"}
