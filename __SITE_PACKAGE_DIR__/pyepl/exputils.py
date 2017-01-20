# PyEPL: exputils.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module implements fundamental features used in most experiments.
"""

import pyepl
import cPickle
import timing
from eeg import EEGTrack
from textlog import LogTrack
from optparse import OptionParser, OptionGroup, Option, OptionValueError
import os, sys, imp, atexit
import hardware
import keyboard
import joystick
import mouse
import display
import sound
import pool
import exceptions

from transarchive import Archive
import random
import time
import weakref


session = None

# set up custom option types...
class EPLOption(Option):
    """
    """
    otypes = {}
    def check_resolution(option, opt, value):
        """
        """
        try:
            # separate the x and y components of the resolution
            xy = value.split("x")

            if len(xy) != 2:
                # make sure there are only 2 components (only one 'x' in the string)
                raise ValueError, value

            # return the value as a 2-tuple of integers
            return (int(xy[0]), int(xy[1]))
        except ValueError:
            # if it couldn't be turned into a 2-tuple of integers, raise an exception
            raise OptionValueError("option %s: invalid resolution value: %r" % (opt, value))
    otypes["resolution"] = check_resolution
    TYPES = Option.TYPES + tuple(otypes.keys())
    TYPE_CHECKER = Option.TYPE_CHECKER.copy()
    TYPE_CHECKER.update(otypes)

class Experiment:
    """
    ...
    
    archive - Directory name for storing all collected data - DEFAULT:
    "data"
    
    subject - String identifier for the current subject
    
    config - File name for the global configuration to be used
    
    sconfig - File name for the individual subject configuration to be
    used
    
    resolution - 2-tuple of the screen resolution to be used -
    DEFAULT: (640, 480)
    
    fullscreen - Boolean, if True, the graphics are run in full screen
    mode - DEFAULT: True
    
    joystick_zero_threshold - The range of small axis position values
    to be reported as 0.0 for joystick axes - DEFAULT 0.2
    
    use_opengl - Boolean, if True, use OpenGL for graphics DEFAULT:
    True
    
    use_eeg - Boolean, if True, automatically create an EEG track for
    while the experiment runs - DEFAULT: True

    sync_to_vbl - Boolean, if True, waits for screen's vertical
    retrace before drawing - DEFAULT: True
    
    max_facet_length - The maximum length, in VR units, for 3D facets.
    Larger facets will be broken into smaller pieces for display.
    DEFAULT: 0.0 (do not break up larger facets)
    
    show_fps - Boolean, if True the display frames per second is shown
    in the corner of the the screen during render loops.
    DEFAULT: False
    """
    # set the default options...
    defaults = {
        "archive": "data",
        "subject": None,
        "config": None,
        "sconfig": None,
        "resolution": (640, 480),
        "fullscreen": True,
        "joystick_zero_threshold": 0.2,
        "use_eeg": True,
        "sync_to_vbl": True,
        "max_facet_length": 0.0,
        "show_fps": False
        }
    def __init__(self, **options):
        """
        Construct the Experiment object.

        INPUT ARGS:
          options- keyword arguments are used to set the initial
          experiment options.
        """
        self.options = Experiment.defaults.copy()
        self.options.update(options)
        self.data = None
        self.experiment = None
        self.subject = None
        self.session = None
        self.state = None
        self.configbackup = None
        self.sconfigbackup = None
        self.eegtrack = None
        self.explog = None
	
	self.didParse = False # for backwards compatibility
	self.didSetup = False
	self.parseArgs()
	self.setup()

    def __del__(self):
        """
        Cleanly shut down PyEPL.
        """
        # log
        if self.explog:
            self.explog.logMessage("EXIT")
        
        # if there's an EEGTrack, delete it
        self.eegtrack = None

        # delete the experiment log
        self.explog = None
        
        # finalize PyEPL
        pyepl.finalize()
    def getOptions(self):
        """
        Return a PoolDict of the options associated with this
        Experiment.
        """
        return pool.PoolDict(**self.options)
    def parseArgs(self, optparser = None, version = None):
        """
        Updates the experiment options using the command line
        arguments.
        
        The positional argument "version" indicates the version of the
        experiment.  The second positional argument, "optparser", is
        optional and can be used to pass in an optparse.OptionParser
        object to specify per-experiment command line options.  A
        group of PyEPL options will be appended to it.  A passed in
        OptionParser must use the EPLOption option class or one
        derived from it.
        """
	if not self.didParse:
	    # bring the defaults into the local scope
	    defaults = Experiment.defaults.copy()
	    
	    # update the default options with any options provided as keyword arguments
	    defaults.update(self.options)

	    if optparser:
		# if an optparser was specified, use it...
		parser = optparser
	    else:
		# ...otherwise, create a new one
		parser = OptionParser(option_class = EPLOption, version = version)

		# create an option group for PyEPL Options
		eplopts = OptionGroup(parser, "PyEPL Options")

	    # add the options to the group...
	    eplopts.add_option("-a", "--archive",
			       dest = "archive", metavar = "DIRECTORY", default = defaults["archive"],
			       help = "Specify alternative path for data storage.  Default: data")
	    eplopts.add_option("-s", "--subject",
			       dest = "subject", metavar = "SUBJECTID", default = defaults["subject"],
			       help = "Indicate a subject to use.")
	    eplopts.add_option("--config",
			       dest = "config", metavar = "CONFIGFILE", default = defaults["config"],
			       help = "Specify the path of the configuration file.")
	    eplopts.add_option("--sconfig",
			       dest = "sconfig", metavar = "CONFIGFILE", default = defaults["sconfig"],
			       help = "Specify the path of the subject configuration file to be copied in.")
	    eplopts.add_option("--resolution", type = "resolution", default = defaults["resolution"],
			       dest = "resolution", metavar = "WIDTHxHEIGHT",
			       help = "Set the graphical resolution for the session.")
	    eplopts.add_option("--no-fs", action = "store_false", default = defaults["fullscreen"],
			       dest = "fullscreen",
			       help = "Run the experiment in a window (not fullscreen).")
	    eplopts.add_option("--js-zero-threshold", type = "float", default = defaults["joystick_zero_threshold"],
			       dest = "joystick_zero_threshold", metavar = "THRESHOLD",
			       help = "Set the range of small axis position values to be reported as 0.0 for joystick axes.")
	    eplopts.add_option("--no-eeg", action = "store_false", default = defaults["use_eeg"],
			       dest = "use_eeg",
			       help = "Run the experiment without automatically creating an EEGTrack.")
	    eplopts.add_option("--no-screen-sync", action = "store_false", default = defaults["sync_to_vbl"],
			       dest = "sync_to_vbl",
			       help = "Do not enable synchronization with the screen's vertical retrace.")
	    eplopts.add_option("--max-facet-length", type = "float", default = defaults["max_facet_length"],
			       dest = "max_facet_length", metavar = "MAXLENGTH",
			       help = "Set the maximum length, in VR units, for 3D facets.  Larger facets will be broken into smaller pieces for display.")
	    eplopts.add_option("--show-fps", action = "store_true", default = defaults["show_fps"],
			       dest = "show_fps", help = "Display frames per second in the corner of the screen during render loops.")

	    # add the group to the optparser
	    parser.add_option_group(eplopts)

	    # parse the command line arguments
	    opts, args = parser.parse_args(sys.argv)

	    if len(args) > 1:
		# exit if positional arguments (not options) are detected
		sys.stderr.write("This program takes no commandline arguments, only options!\n")
		sys.exit(1)

	    # update the options dictionary with the command line arguments
	    self.options.update(opts.__dict__)

	    self.didParse = True

    def setup(self):
        """
        Set up the current subject for logging based on the current
        experiment options.  Initialize PyEPL's hardware interface and
        create an EEGTrack if the option "use_eeg" is true.
        """
	if not self.didSetup:
	    # create the main archive
	    self.data = Archive(self.options["archive"])

	    if self.options["subject"]:
		# if a subject identifier is given, create the subject archive
		self.subject = self.data.createDirectory(self.options["subject"])

	    # to begin with, the session archive is the same as the subject archive
	    self.session = self.subject
	    global session
	    session = self.session

	    # read the global configuration file
	    if self.options["config"]:
		try:
		    self.globalconfig = ConfigurationFile(self.options["config"])
		except IOError, e:
		    if self.options["config"] != "config.py":
			raise e
		    self.options["config"] = None
		    # no config, use a blank one
		    self.globalconfig = Configuration()

	    # if there is a subject archive
	    if self.subject:
		# create the state archive
		self.state = self.subject.createDirectory("state")

		# create the global configuration backup archive
		self.configbackup = self.subject.createDirectory("configbackup")
		
		# create the subject configuration backup archive
		self.sconfigbackup = self.subject.createDirectory("sconfigbackup")
		
		# produce the config backup file name to use
		fn = str(int(time.time())) + "XXX.py"

		if self.options["config"]:
		    # if there is a global configuration file specified, copy it into the subject archive
		    self.subject.createFile("config.py").write(open(self.options["config"]).read())

		    # now back it up
		    self.configbackup.createFile(fn).write(open(self.options["config"]).read())
		else:
		    # otherwise try using config.py...
		    try:
			self.subject.createFile("config.py").write(open("config.py").read())
			
			# now back it up
			self.configbackup.createFile(fn).write(open("config.py").read())
		    except:
			# no config.py?  fine.  we'll deal
			pass

		if self.options["sconfig"]:
		    # if there is a subject configuration file specified, copy it into the subject archive
		    self.subject.createFile("sconfig.py").write(open(self.options["sconfig"]).read())

		    # now back it up
		    self.sconfigbackup.createFile(fn).write(open(self.options["sconfig"]).read())

	    # initialize PyEPL
	    pyepl.initialize(**self.options)

	    # log
	    if self.session:
		self.explog = LogTrack("experiment")
		self.explog.logMessage("SETUP")

	    self.didSetup = True

    def getConfig(self):
        """
        Return the Configuration object for the current subject.
        """
        # is there a subect set up?
        if self.subject:
            # if so, use the config files from the subject directory
            return parentChildFileConfig(self.subject.createFile("config.py"), self.subject.createFile("sconfig.py"))
        else:
            # otherwise...
            if self.options["config"]:
                # if a global config file is in the options, use it
                return ConfigurationFile(self.options["config"])
            try:
                # none specified?  try config.py
                return ConfigurationFile("config.py")
            except IOError:
                # no config.py?  use a blank configuration
                return Configuration()

    def setSession(self, sessionname):
        """
        Specify a session name to be used for subsequently created tracks.
        Data will be stored in an appropriately named subdirectory of the
        subject directory rather than directly in the subject directory.

        INPUT ARGS:
        sessionname- A string which names this session.  This string is used to name the directory containing this run's data files.

        """
        # create and set the session archive
        self.session = self.subject.createDirectory("session_%s" % sessionname)
        global session
        session = self.session

        # make an eeg track if needed...
        if self.options["use_eeg"] and not self.eegtrack:
            self.eegtrack = EEGTrack("eeg")

        # move the eeg log target...
        elif self.eegtrack:
            self.eegtrack.newTarget(self.session)

        # log
        if self.explog:
            self.explog.logMessage("SESSION\t%s" % sessionname)

    def breakfunc(self, pressed, timestamp, expcb):
        # we only care if the button is pressed, not released...
        if pressed:
            # if there is an EEGTrack, delete it
            self.eegtrack = None
            
            # Stop any currently playing videos
            video = display.VideoTrack.lastInstance()
            if video:
                video.stopAllMovies()

            # log
            if self.explog:
                self.explog.logMessage("BREAK")

            # delete the experiment log
            self.explog = None

            # if there is an experiment break callback...
            if expcb:
                # ...call it...
                if expcb():
                    # ...and if it returns a true value, exit
                    print "BREAK!"
                    pyepl.finalize()
                    sys.exit()
            else:
                # if there was no experiment break callback, just exit
                print "BREAK!"
                pyepl.finalize()
                sys.exit()

    def setBreak(self, button = None, callback = None):
        """
        After this call, PyEPL will flush all tracks on exit, even if the
        program crashes.  If the argument "button" is given, then pressing
        the specified button will cause the program to exit.  If the
        argument "callback" is given, the provided callable will be called
        prior to exitting.  If the exit was triggered by the break button,
        the callback must return a true value, or the program will not
        exit.

        INPUT ARGS:
        button- The Button object which represents the keyboard button that when pressed triggers a break.  (Default: button=Key("ESCAPE") & Key("F1"))
        callback- A callable which is called prior to exitting.

        """
        if button is None:
            button = keyboard.Key("ESCAPE") & keyboard.Key("F1")
        atexit.register(self.__del__)
        if callback:
            atexit.register(callback)
        self.breakcb = self.breakfunc
        button.addCallback(self.breakcb, callback)
        self.breakButton = button

    def saveState(self, instate, **items):
        """
        Save any picklable objects as the state for the current
        subject.  The optional positional argument "instate" takes a
        State object.  The call will save all the data in the State
        object except that any values in the State object may be
        overridden by providing the new values as keyword arguments.
        Returns the state as it was saved.

        INPUT ARGS:
          instate- The State object         
        """
        # if there is a state archive...
        if not self.state is None:
            # combine instate with items
            instate = State(instate, **items)

            # pickle the state to a file named after the current time
            cPickle.dump(instate, self.state.createFile(str(timing.now()) + ".pickle"), -1)

        # log
        if self.explog:
            self.explog.logMessage("SAVESTATE")

        # return the saved state
        return instate
    def restoreState(self):
        """
        Return a State object for the most recently saved state.
        """
        # log
        if self.explog:
            self.explog.logMessage("RESTORESTATE")
        
        # if there is a state archive...
        if not self.state is None:
            # get the file names in the state archive
            listing = self.state.listDir()

            # if there are any files in the archive...
            if len(listing):
                # calculate the timestamp of the most recently saved state based on the file names
                statetime = max(map(lambda filename: long(os.path.splitext(filename)[0]), listing))

                # unpickle the file named after the calculated timestamp, returning the result
                return cPickle.load(self.state.open(str(statetime) + ".pickle"))
        # if there is no state archive, or no state files, return None
        return None

class PresentationClock:
    """
    A presentation clock is an abstraction used for timing to keep the
    timing of input and output as accurate as possible.  The clock
    keeps a virtual time which does not advance with the real time.
    Instead, it advances when you tell it to.  You can pass the
    PresentationClock into timed output routines and they will not
    perform the actual output until the real time has caught up the
    the virtual time.

    A good way to think about it is that the time in the
    PresentationClock is when you want the next output action
    (presentation) to occur.  Passing the PresentationClock into input
    routines will advance the virtual clock to the moment of the input
    that the routine waited for.
    """
    def __init__(self,correctAccumulatedErrors=False):
        """
        Create a PresentationClock set to the time of its creation.
        """
        # start the clock at the current time
        self.tare()

        # save whether to correct the accumulated errors
        self.correctAccumulatedErrors=correctAccumulatedErrors
        
        # keep track of the accumulated timing error in ms
        # is in terms of (Actual - Expected)
        self.resetAccumulatedTimingError()
    def resetAccumulatedTimingError(self):
        """
        Reset the accumulated timing error to zero.
        """
        self.accumulatedTimingError = 0
    def tare(self, t = None):
        """
        Set the clock to the current time, or to the time specified.

        INPUT PARAMS:
          t- the time in milliseconds to set the clock to.  (alternatively, this can be a 2-tuple, the first element contains time in milliseconds.)
        
        """
        if t is None:
            # if called with no parameters, set the clock to the current time
            self.virtualtime = timing.now()
        elif isinstance(t, tuple):
            # if called with a tuple, set the clock to the first element of the tuple (to support timestamps with maximum latency)
            self.virtualtime = t[0]
        else:
            # otherwise, set the time to the given paramenter (in milliseconds)
            self.virtualtime = t
    def delay(self, milliseconds, jitter = None, resolveTimingError=False):
        """
        Advance the clock by the number of milliseconds given.
        Optionally add a random amount of time up to the given jitter
        (in milliseconds).

        INPUT ARGS:
          milliseconds- number of milliseconds to advance the clock
          jitter- if this OPTIONAL argument is specified, then the
            clock is advanced a random number of milliseconds between 0
            and the value of this parameter, in addition to the clock
            advance due to the milliseconds parameter.
            
          resolveTimingError- Optional argument that defaults to
            False.  This will adjust the requested milliseconds by the
            accumulated error from previous timedCalls with this
            clock.  Accumulated error can occur in a number of ways.
            For example, if you requested an updateScreen to occur at
            a specific time t based on the presentation clock's
            virtual time, but the updateScreen actually occurred at
            time t+5 because it is timed to the screen refresh, you
            would have an accumulated error of 5ms.  In this case, you
            would need to subtract 5ms from the milliseconds delay to
            make sure that the next stimulus comes on the screen when
            you desire.
          
        """
        if jitter:
            # if jitter is given, translate this into a call to jitter
            # and set actual milliseconds used
            milliseconds = self.jitter(milliseconds, milliseconds + jitter, resolveTimingError)
        else:
            # otherwise, add milliseconds to the virtual time
            # see if we must resolve the timing error
            if self.correctAccumulatedErrors or resolveTimingError:
                # adjust the milliseconds and reset the accumulatedTimingError
                milliseconds -= self.accumulatedTimingError
                if milliseconds < 0:
                    self.accumulatedTimingError = -milliseconds
                    milliseconds = 0
                    exceptions.eplWarn("Unable to account for %dms of timing error." % 
                                       (self.accumulatedTimingError))
                else:
                    self.accumulatedTimingError = 0
            # extend the virtual time        
            self.virtualtime += milliseconds

        # return the milliseconds (to see if changed)
        return milliseconds
    def jitter(self, low_milliseconds, high_milliseconds = None, resolveTimingError=False):
        """
        Advances the clock by a random number of milliseconds.

        INPUT ARGS:
        
          ms1 & ms2- If one argument is specified, delay a random
            amount of time between 0 and the value of the parameter
            (in milliseconds).  if two parameters, delay a random
            amount of time between the values of the first and second
            parameters (in milliseconds)

          resolveTimingError- see the help for delay.
        """
        if high_milliseconds is None:
            # if called with only one parameter, delay a random amount of time between 0 and the value of the parameter (in milliseconds)
            t = random.randint(0, low_milliseconds)
        else:
            # if two parameters, delay a random amount of time between the values of the first and second parameters (in milliseconds)
            t = random.randint(low_milliseconds, high_milliseconds)

        # return the amount of time actually delayed
        return self.delay(t,resolveTimingError=resolveTimingError)
    def get(self):
        """
        Retrieves the clock's virtual time.
        OUTPUT ARGS:
        
          time- time in milliseconds when the clock is set for.
        """
        # return the clock's virtual time
        return self.virtualtime
    def wait(self):
        """
        Wait until the current time catches up to the clock.
        """
        # as long as the current time is less than (earlier than) the virtual time...
        while timing.now() < self.virtualtime:
            # do nothing (poll for events)
            hardware.pollEvents()

class Configuration:
    """
    """
    def overlay(self, config):
        """
        """
        # return a ConfigurationOverlayed object made from this Configuration and the given config
        return ConfigurationOverlayed(self, config)
    def sequence(self, sequenceposition):
        """
        """
        # return a ConfigurationSequenced object made from this Configuration and the given config
        return ConfigurationSequenced(self, sequenceposition)
    def domain(self, domainname):
        """
        """
        # return a ConfigurationDomained object made from this Configuration and the given config
        return ConfigurationDomained(self, domainname)

class ConfigurationFile(Configuration):
    """
    """
    def __init__(self, filenameorfile, extra_locals = None):
        """
        """
        if isinstance(filenameorfile, file):
            # if this is a file, get its name
            filename = filenameorfile.name
        else:
            # otherwise, use the parameter directly as a file name
            filename = filenameorfile
            
        # create the globals for the config execution environment
        g = {"__builtins__": __builtins__,
             "Key": keyboard.Key,
             "JoyButton": joystick.JoyButton,
             "JoyAxis": joystick.JoyAxis,
             "JoyBall": joystick.JoyBall,
             "JoyHat": joystick.JoyHat,
             "MouseButton": mouse.MouseButton,
             "MouseAxis": mouse.MouseAxis,
             "MouseRoller": mouse.MouseRoller,
             "Text": display.Text,
             "Image": display.Image,
             "SolidBackground": display.SolidBackground,
             "Font": display.Font,
             "Color": display.Color,
             "AudioClip": sound.AudioClip,
             "PoolDict": pool.PoolDict,
             "Pool": pool.Pool,
             "TextPool": pool.TextPool,
             "ImagePool": pool.ImagePool,
             "SoundPool": pool.SoundPool,
             "Sequence": Sequence,
             "passive": self.passiveSet}

        if extra_locals:
            # if locals were passed in, copy them
            self.config = extra_locals.copy()
        else:
            # otherwise, create an empty dictionary as the locals
            self.config = {}

        # execute the config module
        execfile(filename, g, self.config)
    def passiveSet(self, **kw):
        """
        """
        for name, value in kw.iteritems():
            if not self.config.has_key(name):
                self.config[name] = value
    def __getattr__(self, name):
        """
        """
        try:
            # try looking up the name in the config dictionary and returning the value
            return self.config[name]
        except KeyError:
            # if it wasn't found, raise an exception
            raise AttributeError, "Configuration has no attribute: %s" % name

class ConfigurationOverlayed(Configuration):
    """
    """
    def __init__(self, config1, config2):
        """
        """
        # save the two source configs...
        self.config1 = config1
        self.config2 = config2
    def __getattr__(self, name):
        """
        """
        if hasattr(self.config2, name):
            # try returning the value from config2
            return getattr(self.config2, name)

        # didn't work?  try from config1.
        return getattr(self.config1, name)

def parentChildFileConfig(parent, child):
    """
    """
    return ConfigurationFile(parent, extra_locals = ConfigurationFile(child).config).overlay(ConfigurationFile(child))

class ConfigurationSequenced(Configuration):
    """
    """
    def __init__(self, config, seqpos):
        """
        """
        # save the source config and the sequence position...
        self.config = config
        self.seqpos = seqpos
    def __getattr__(self, name):
        """
        """
        # if we're looking for "seq" and our config has a "seq"...
        if name == "seq" and hasattr(self.config, "seq"):
            # return the sequence at our sequence position
            return self.config.seq[self.seqpos]

        # if our config has a "seq"...
        if hasattr(self.config, "seq"):
            try:
                # attempt to return the value from self.seq
                return getattr(self.seq, name)
            except AttributeError:
                pass
            except IndexError:
                pass

        # not there?  try getting from self.config
        return getattr(self.config, name)

class ConfigurationDomained(Configuration):
    """
    """
    def __init__(self, config, domainname):
        """
        """
        # save the source config and domainname
        self.config = config
        self.domainname = domainname
    def __getattr__(self, name):
        """
        """
        # calculate the qualified name to look for first
        n = "%s_%s" % (self.domainname, name)

        if hasattr(self.config, n):
            # try returning the value of the qualified name
            return getattr(self.config, n)

        # not there?  try the original name.
        return getattr(self.config, name)

class State:
    """
    """
    def __init__(self, instate = None, **items):
        """
        """
        # if instate is given...
        if instate:
            # set self.items to a copy of the items dictionary of instate
            self.__dict__["items"] = instate.items.copy()

            # update self.items with the keyword arguments (items)
            self.items.update(items)
        else:
            # otherwise, set self.items to the keyword arguments (items)
            self.__dict__["items"] = items
    def __getstate__(self):
        """
        """
        # return the items dictionary
        return self.items
    def __setstate__(self, s):
        """
        """
        # set the items dictionary to the state value
        self.__dict__["items"] = s
    def __getattr__(self, name):
        """
        """
        try:
            # try looking up and returning the value from the items dictionary
            return self.items[name]
        except KeyError:
            # if it's not there, raise an exception
            raise AttributeError, "No such state attribute: %s" % name
    def __setattr__(self, name, value):
        """
        """
        # set the value in the items dictionary
        self.items[name] = value
    def update(self, **items):
        """
        """
        # just use the update method of the items dictionary
        self.items.update(items)

class Sequence:
    """
    """
    def __init__(self, *dimensions):
        """
        """
        # create the sequence list
        self.__dict__["sequ"] = []

        # if there are any dimensions to this sequence...
        if len(dimensions):
            # iterate over the elements of the first one...
            for x in xrange(dimensions[0]):
                # ...appending Sequences to the sequence list for each
                # the appended Sequences take the remaining dimensions
                self.sequ.append(Sequence(*dimensions[1:]))

        # create an emtpy dictionary to hold the attributes set on this Sequence
        self.__dict__["items"] = {}
    def __len__(self):
        """
        """
        # return the length of the sequence list
        return len(self.sequ)
    def __getitem__(self, index):
        """
        """
        # if the index is a tuple (multidimensional index)...
        if isinstance(index, tuple):
            if not isinstance(index[0], int):
                # if the first element of the index is not an integer, return a SequenceSlice
                return SequenceSlice(self, index)
            
            if len(index) == 2:
                # there's only one dimension left, so index the sub-Sequence without a tuple
                return self.sequ[index[0]][index[1]]
            else:
                # there are more dimensions, use a tuple
                return self.sequ[index[0]][index[1:]]

        # if the index is not an integer...
        if not isinstance(index, int):
            # return a SequenceSlice
            return SequenceSlice(self, (index,))

        # otherwise, return the sub-Sequence found at that index
        return self.sequ[index]
    def __getattr__(self, name):
        """
        """
        try:
            # try returning the value from the items dictionary
            return self.items[name]
        except KeyError:
            # if it's not there, raise an exception
            raise AttributeError, "No such sequence attribute: %s" % name
    def __setattr__(self, name, value):
        """
        """
        # set the attribute as an item in the items dictionary
        self.items[name] = value

class SequenceSlice:
    """
    """
    def __init__(self, seq, index):
        """
        """
        # save the sequence and the index
        self.__dict__["seq"] = seq
        self.__dict__["index"] = index
    def __getattr__(self, name):
        """
        """
        # start with an empty list
        r = []

        # if our index is multidimensional...
        if len(self.index) > 1:
            # iterate over the integers appropriate for the slice object in the first dimension...
            for x in xrange(*self.index[0].indices(len(self.seq))):
                # index the element of the sequence with the remaining dimensions, appending the result
                r.append(getattr(self.seq[x][self.index[1:]], name))
        else:
            # only one dimension - iterate over the integers appropriate for the slice object...
            for x in xrange(*self.index[0].indices(len(self.seq))):
                # append the element of the sequence
                r.append(getattr(self.seq[x], name))

        # return the list
        return r
    def __setattr__(self, name, value):
        """
        """
        # 
        if isinstance(value, tuple) or isinstance(value, list):
            i = iter(value)
            if len(self.index) > 1:
                for x in xrange(*self.index[0].indices(len(self.seq))):
                    setattr(self.seq[x][self.index[1:]], name, i.next())
            else:
                for x in xrange(*self.index[0].indices(len(self.seq))):
                    setattr(self.seq[x], name, i.next())
        else:
            if len(self.index) > 1:
                for x in xrange(*self.index[0].indices(len(self.seq))):
                    setattr(self.seq[x][self.index[1:]], name, value)
            else:
                for x in xrange(*self.index[0].indices(len(self.seq))):
                    setattr(self.seq[x], name, value)
