# PyEPL: sound.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides functions for playing and recording sounds.
"""

# import python modules
import time
import threading
import numpy
import math
import struct
import copy
import string
from os import uname
from struct import unpack

# import pyepl modules
from transarchive import Archive
import textlog
from base import MediaFile
import exputils
import timing
import exceptions
import hardware
import exputils
from stimulus import Stimulus
from hardware import addPollCallback, removePollCallback, SoundFile
from exceptions import EPLFatalError

class SoundException(EPLFatalError):
    def __init__(self, msg):
        EPLFatalError.__init__(self, msg)
    def printMsg(self):
        print "SoundException: ", self.__str__()

class AudioClip(Stimulus):
    """
    Manages sound data.
    """
    def __init__(self, data=None):
	self.snd = data
	# constants: 
	self.RESAMPLEDRATE = 44100
	self.sampleWidth = 2
	self.numchannels = 2

    def getDuration(self):
        """
        Return the duration of an AudioClip in milliseconds.

        OUTPUT ARGS:
          duration- returns length of AudioClip object in milliseconds.
          
        """
	self.duration = (len(self.snd)*1000) / (self.RESAMPLEDRATE
						* self.sampleWidth 
						* self.numchannels)
        return self.duration

    def stripChannel(self, rawstr):
        """
        Strip the second channel from raw data in str form for saving.
        """
        # Convert to numeric array
        xbuff = numpy.array(struct.unpack(str(len(rawstr)/self.sampleWidth) + 'h', rawstr), dtype=numpy.int16)
	# Drop a channel
        xbuff = xbuff[::2]

        # convert to a string
        newstr = xbuff.tostring()
        del xbuff
        return newstr
                
    def duplicateChannel(self, rawstr):
	""" 
	Copy the data of a one-channel signal into another channel, to
	make a 2-channel signal.
	"""
	# add the second channel
	xbuff = numpy.zeros((len(rawstr)*2), dtype=numpy.int16)
	xbuff[::2] = rawstr;
	xbuff[1::2] = rawstr;

	# convert to a string
	sbuff = xbuff.tostring()
	del xbuff 
	return sbuff

    def append(self, data, numchans):
	if not self.snd:
	    self.snd = ''
	if numchans==1:
	    # double the data 
	    buff = numpy.array(struct.unpack(str(len(data)/self.sampleWidth) + 'h', data), dtype=numpy.int16)
	    data = self.duplicateChannel(buff)

	self.snd += data

    def present(self, clk = None, duration = None, jitter = None, bc = None, minDuration = None, doDelay = True):
        """
        Present an AudioClip.  If provided, the clock will be advanced
        by the duration/jitter passed in, otherwise it will advance
        the duration of the audio clip.  If a ButtonChooser is
        provided, then present waits until the button is pressed
        before returning, advancing the clock to the point when the
        button was pressed.

        INPUT ARGS:
          clk- Optional PresentationClock for timing.
          duration/jitter- Duration to keep the stimulus on.
          bc - Optional ButtonChooser object.

        OUTPUT ARGS:
          timestamp- time and latency of when the sound was played.
          button- Button pressed if we passed in bc.
          bc_time- Time and latency of when the button was pressed (if provided)
        """

        a = AudioTrack.lastInstance()

        # get the clock if needed
        if clk is None:
            clk = exputils.PresentationClock()

	# play the sound
        timestamp = a.play(self, t=clk, doDelay=doDelay)

        if bc:
            # wait for button press
            button,bc_time = bc.waitWithTime(minDuration, duration, clk)
            return timestamp, button, bc_time
        elif duration:
            # reset to before play and just advance the duration+jitter
            clk.delay(duration, jitter)
            return timestamp
        else:
            # keep the clock advanced the duration of the sound
            return timestamp
    
    def __add__(self,clip):
        """
        Add two AudioClips together, aligning to the beginning of both
        and returning a clip the length of the longer clip.
        """

        # convert from str to numpy array
        base = self.stripChannel(self.snd)
        toadd = self.stripChannel(clip.snd)
        base = numpy.array(struct.unpack(str(len(base)/self.sampleWidth) + 'h', base), dtype=numpy.int16)
	toadd = numpy.array(struct.unpack(str(len(toadd)/clip.sampleWidth) + 'h', toadd), dtype=numpy.int16)

        # see the diff in length
        clipdiff = len(base) - len(toadd)

        if clipdiff > 0:
            # append zeros to the clip
            toadd = numpy.concatenate([toadd,numpy.zeros(clipdiff)])
        elif clipdiff < 0:
            # append zeros to the base
            base = numpy.concatenate([base,numpy.zeros(-clipdiff)])

        newclip = base+toadd*.5
        newclip = self.duplicateChannel(newclip)
        return AudioClip(newclip)


class Beep(AudioClip):
    def __init__(self, freq, duration, risefalltime = 0, scalePercent = 0.8):
	"""
	Generate a beep of desired frequency, duration, and rise/fall
	time.  Format of beep is in 16bit int samples.
	
        INPUT ARGS:
          freq- frequency of beep
          duration- length of time (in ms.) to play beep for.
          risefalltime- length of time (in ms.) for beep to rise from
            silence to full volume at beginning, and fall to no volume
            at end.
          scalePercent- Percent of the max audio range for the beep (defaults to .8).

	  """
	AudioClip.__init__(self)
	a = AudioTrack.lastInstance()
        
        # set the scale
	scale = a.eplsound.SCALE * scalePercent

	# Do some rate and ms conversions
	sampCycle = int(self.RESAMPLEDRATE/freq)
	sampDur = int(duration*self.RESAMPLEDRATE/1000)
	sampRise = int(risefalltime*self.RESAMPLEDRATE/1000)

	# Create the array at correct frequency
	buff = numpy.arange(0, sampDur*(2*math.pi)/sampCycle, (2*math.pi)/sampCycle)
	buff = scale * numpy.sin(buff)

	# Apply envelope
	if risefalltime > 0:
	    env = numpy.arange(0, 1, float(1/float(sampRise)))
	    buff[0:len(env)] = buff[0:len(env)]*env
	    buff[-1:-(len(env)+1):-1] = buff[-1:-(len(env)+1):-1]*env
	    
	# convert to int16
	buff = buff.astype(numpy.int16)

	# convert duplicate to a 2nd channel
	self.snd = self.duplicateChannel(buff)
    

# map strings to SoundFile constants:
formatDict = {'aiff':SoundFile.SF_FORMAT_AIFF,
	      'alaw':SoundFile.SF_FORMAT_ALAW,
	      'au':SoundFile.SF_FORMAT_AU,
	      'avr':SoundFile.SF_FORMAT_AVR,
	      'htk':SoundFile.SF_FORMAT_HTK,
	      'ima_adpcm':SoundFile.SF_FORMAT_IMA_ADPCM,
	      'ircam':SoundFile.SF_FORMAT_IRCAM,
	      'mat4':SoundFile.SF_FORMAT_MAT4,
	      'mat5':SoundFile.SF_FORMAT_MAT5,
	      'ms_adpcm':SoundFile.SF_FORMAT_MS_ADPCM,
	      'nist':SoundFile.SF_FORMAT_NIST,
	      'paf':SoundFile.SF_FORMAT_PAF,
	      'pvf':SoundFile.SF_FORMAT_PVF,
	      'raw':SoundFile.SF_FORMAT_RAW,
	      'sds':SoundFile.SF_FORMAT_SDS,
	      'svx':SoundFile.SF_FORMAT_SVX,
	      'ulaw':SoundFile.SF_FORMAT_ULAW,
	      'voc':SoundFile.SF_FORMAT_VOC,
	      'adpcm':SoundFile.SF_FORMAT_VOX_ADPCM,
	      'w64':SoundFile.SF_FORMAT_W64,
	      'wav':SoundFile.SF_FORMAT_WAV,
	      'wavex':SoundFile.SF_FORMAT_WAVEX,
	      'xi':SoundFile.SF_FORMAT_XI}

widthDict = {'short':SoundFile.SF_FORMAT_PCM_16,
	     'pcm24':SoundFile.SF_FORMAT_PCM_24,
	     'pcm32':SoundFile.SF_FORMAT_PCM_32,
	     'sbyte':SoundFile.SF_FORMAT_PCM_S8,
	     'ubyte':SoundFile.SF_FORMAT_PCM_U8,
	     'double':SoundFile.SF_FORMAT_DOUBLE,
	     'dpcm16':SoundFile.SF_FORMAT_DPCM_16,
	     'dpcm8':SoundFile.SF_FORMAT_DPCM_8,
	     'dwvw12':SoundFile.SF_FORMAT_DWVW_12,
	     'dwvw16':SoundFile.SF_FORMAT_DWVW_16,
	     'dwvw24':SoundFile.SF_FORMAT_DWVW_24,
	     'dwvwn':SoundFile.SF_FORMAT_DWVW_N,
	     'float':SoundFile.SF_FORMAT_FLOAT,
	     'g721_32':SoundFile.SF_FORMAT_G721_32,
	     'g723_24':SoundFile.SF_FORMAT_G723_24,
	     'g723_40':SoundFile.SF_FORMAT_G723_40,
	     'gsm610':SoundFile.SF_FORMAT_GSM610}

endianDict = {'big':SoundFile.SF_ENDIAN_BIG,
	      'cpu':SoundFile.SF_ENDIAN_CPU,
	      'file':SoundFile.SF_ENDIAN_FILE,
	      'little':SoundFile.SF_ENDIAN_LITTLE}

defaultFileSettings = {'format':'wav', 'sampleWidth':'short', 'channels':1, 
		       'sampleRate':44100, 'endian':'little'}

class FileAudioClip(MediaFile,AudioClip):
    """ 
    Class to wrap sound data either being played from or saved to file.      
    """
    def __init__(self, *args, **fileargs):
	"""
	Construct a FileAudioClip.  The constructor takes 1 or 2
	positional arguments followed by 0 to 5 keyword arguments.

	POSITIONAL ARGUMENTS: 
	For a play-mode FileAudioClip, pass a single positional argument
	with the path+filename of the sound-file to be played, or the
	path+filename followed by a dict with the keyword settings
	described under "KEYWORD ARGUMENTS".  For a record-mode AudioClip,
	pass 2 positional arguments:  pass an archive object for
	directing the recorded file as the first argument, and the
	desired name for the output file as the second.

	KEYWORD ARGUMENTS: 

	These are only necessary for opening raw sound files.  If you
	need to open a file containing raw sound data, you must supply
	the constructor with the keyword argument format='raw'.  The
	following are the default settings for opening raw sound data.
	They can be overridden by passing alternate values as
	additional keyword arguements.

	sampleWidth=='short'
	channels==1
	sampleRate==44100
	endian=='little'

	Currently, the following settings are available for these
	fields:

	sampleWidth: may be any of the following strings:
	short, pcm24, pcm32, sbyte, ubyte, double, dpcm16, dpcm8,
	dwvw12, dwvw16, dwvw24, dwvwn, g721_32, g723_24, g723_40,
	gsm610

	channels: any positive integer, usually 1 or 2.

	sampleRate: any positive integer, usually 22050 or 44100.

	endian: may be any of the following strings:
	big, cpu, file, little
	"""
	AudioClip.__init__(self)

	# PLAY MODE
        if len(args)==1 and isinstance(args[0],str):
            #if there's one arg and its a string, assume its the filename of an existing file
            self.filename=args[0]
	elif len(args)==2 and isinstance(args[1],dict):
	    self.filename = args[0]
	    fileargs = args[1]

	# register file options passed, if any
	self.fileSettings = copy.copy(defaultFileSettings)
	for key in fileargs.keys():
	    # make sure it's a real field
	    try:
		val = self.fileSettings[key]
	    except KeyError:
		raise SoundException('invalid field setting.')
	    val = fileargs[key]
	    # downcase the string args
	    if isinstance(val, str):
		val = string.lower(val)
	    self.fileSettings[key] = val

	# RECORD MODE
        if len(args)==2 and isinstance(args[1],str):
            # we are opening a new file
            archive = args[0]
            fname = archive.fullPath() + "/" + args[1]
            self.filename = fname + '.' + self.fileSettings['format']

	    soundfile = SoundFile.soundFile(self.filename, SoundFile.SFM_WRITE, 
					    formatDict['wav'] \
					    | widthDict[self.fileSettings['sampleWidth']],
					    self.fileSettings['channels'], 
					    self.fileSettings['sampleRate'])
	    del soundfile

        #initially, the file isn't loaded into memory
	self.sndStripped=None
        self.duration = None

    def getDuration(self):
        """
        Return the duration of an AudioClip in milliseconds.

        OUTPUT ARGS:
          duration- returns length of AudioClip object in milliseconds.
          
        """
        if self.duration is None:
            self.load()
            self.unload()
        return self.duration

    
    def load(self):
        """
        Load the instance of the sound into memory.
        """
	sizes = '-bh-i---l'
        if not self.snd: #if it's not loaded
	    try:
		mode = SoundFile.SFM_READ
		if self.fileSettings['format']=='raw':
		    format = formatDict[self.fileSettings['format']] \
			| widthDict[self.fileSettings['sampleWidth']] \
			| endianDict[self.fileSettings['endian']]
		    # load the snd-file
		    sfile = SoundFile.soundFile(self.filename, mode, format, self.fileSettings['channels'],
						self.fileSettings['sampleRate'])
		else:
		    sfile = SoundFile.soundFile(self.filename, mode)
		# resample and read into a string
		data = sfile.readfile_short(self.RESAMPLEDRATE)
		self.fileSettings['channels'] = sfile.getChannels()
		nf = sfile.getFrames()
		del sfile
		if uname()[4].find('Power')>=0: # handle Mac endian-ness difference
		    byteorder = '>'
		else:
		    byteorder = '<'
	    except:
		raise SoundException("Couldn't open sound file %s, exiting." % self.filename)

	    # save the raw data to an array
	    totalSamples = nf*self.fileSettings['channels']
	    self.snd = numpy.array(unpack(byteorder + str(totalSamples) + sizes[self.sampleWidth], data), dtype=numpy.int16)
	    if len(self.snd)==0:
		raise SoundException("Sound file %s is empty." % self.filename)

	    # calculate the duration
	    self.duration = (len(data)*1000) / (self.RESAMPLEDRATE
						* self.sampleWidth 
						* self.fileSettings['channels'])

	    # duplicate channel if necessary
	    if self.fileSettings['channels'] == 1:
		# duplicate it
		self.snd = self.duplicateChannel(self.snd)	
	    else:
		# just convert to string.
		self.snd = self.snd.tostring()

    def append(self, data, numchans):
        """
        Append data to an audio clip.
        INPUT ARGS:
          data- raw audio bytes to add at the end of this AudioClip object
	  numchans- the number of channels in the data-argument
        """
	soundFile = SoundFile.soundFile(self.filename, SoundFile.SFM_RDWR, 
					formatDict[self.fileSettings['format']] \
					| widthDict[self.fileSettings['sampleWidth']],
					self.fileSettings['channels'], 
					self.fileSettings['sampleRate'])

	if self.fileSettings['channels']==1 and numchans==2:
	    # strip the second channel
	    channelCorrectData = self.stripChannel(data)
	elif self.fileSettings['channels']==2 and numchans==1:
	    # duplicate the data so we have 2 channels
	    channelCorrectData = self.duplicateChannel(data)
	else:
	    # number of channels to append matches the number of channels in soundfile
	    channelCorrectData = data

	# append the data
	soundFile.append_short(channelCorrectData,
			       len(channelCorrectData)/widthDict[self.fileSettings['sampleWidth']])
	
	del soundFile

        # If the sound is loaded, append to the loaded sound, too
        if self.snd:
	    AudioClip.append(self, data, numchans)	    

    def unload(self):
        """
        Unloads the AudioClip's data from memory.  This frees the memory used by the sound data.
        """
        self.snd = None
	self.sndStripped = None

    def isLoaded(self):
        """
        Tells if the AudioClip is loaded in memory.

        OUTPUT ARGS:
          Returns True if the AudioClip is loaded in memory, False if not.
        """
        return self.snd is not None


class AudioTrack(textlog.LogTrack):
    """
    Provides audio I/O functionality.
    """
    trackTypeName = "AudioTrack"
    logExtension = ".sndlog"
    def __init__(self, basename, archive = None, autoStart = True):
        """
        Prepare the audio track.
        """
        # init the sound class
	self.eplsound = hardware.EPLSound()

        # see if can play and record
        if self.eplsound.getPlayChans() > 0:
            self.canPlay = True
        else:
            self.canPlay = False
        if self.eplsound.getRecChans() > 0:
            self.canRecord = True
        else:
            self.canRecord = False

        # set up the track for loggin
        textlog.LogTrack.__init__(self, basename, archive, autoStart)
        if not archive:
            archive = exputils.session
        self.archive = archive
        self.recording = False
	self.playing = False

        # some parameters that control recording and playing
        self.rec_interval = 1000
	# maximum time (in seconds) we'll append to buffer
	self.MAX_APPEND = .5 # in seconds
	self.play_interval = 250
	self.bytes_per_sample = self.eplsound.FORMAT_SIZE * self.eplsound.NUM_CHANNELS
	self.bytes_per_append = int(math.floor(self.MAX_APPEND * self.eplsound.SAMPLE_RATE \
					       * self.bytes_per_sample))    
	self.currentClip = None

    def startLogging(self):
        """
        Begin logging audio events.
        """
        textlog.LogTrack.startLogging(self)

    def stopLogging(self):
        """
        End logging audio events.
        """
        textlog.LogTrack.stopLogging(self)

    def startService(self):
        """
        Create the sound system and start the stream.
        """
	self.eplsound.startstream()


    def stopService(self):
        """
        Clean up the sound system.
        """
	self.playStop()
        self.stopRecording()
	self.eplsound.stopstream()
        
    def play(self, soundClip, t = None, ampFactor=1.0, doDelay=True):
        """
        Play an AudioClip and return the time and latency of when the
        sound played.

        INPUT ARGS:
          soundClip- AudioClip object of the sound to be played
          t- Optional PresentationClock for timing.
          ampFactor- Optional amplification of sound.  (default value is 1)
          doDelay- Optionally do not tare and move the presentation clock
            forward.  Defaults to True (moving the clock forward)
          
        OUTPUT ARGS:
          timestamp- time and latency when sound playing began.
          
        """          

	# Must be sure to not get multiple callbacks at once, so
	# playing a soundclip while another is running causes that 
	# other one to stop immediately, even if it is not done playing.
	# self.playStop()

	# handle special case: if it's a FileAudioClip and needs loading,
	# load it.
	self.currentClip = soundClip
        if isinstance(soundClip, FileAudioClip):
	    if not soundClip.isLoaded():
		# load and append the sound
		soundClip.load()
	    # for logging
	    shortName = soundClip.filename
	else:
	    shortName = "NOFILE"

        if isinstance(t, exputils.PresentationClock):
            clk = t
	else:
	    clk = exputils.PresentationClock()
	
	t = clk.get()

        if not soundClip.snd is None:
	    # first, compute how many bytes our initial chunk
	    # to append is. ASSUMPTION: always starting from byte 0.
	    firstbytes = min(self.bytes_per_append, len(soundClip.snd))
	    self.total_samples = int(math.floor(len(soundClip.snd)/self.eplsound.FORMAT_SIZE))

	    if self.playing:
		# stop the playing sound 5ms prior to the new time
		timing.timedCall(t-5, self.playStop, False)
	    self.playing = True
	    self.eplsound.resetSamplesPlayed()
	    (timeInterval, appended) = timing.timedCall(t,
						       self.eplsound.append,
						       soundClip.snd[0:firstbytes],
						       len(soundClip.snd[0:firstbytes])/self.eplsound.FORMAT_SIZE,
						       0, ampFactor)
    
            if doDelay:
                # accumulate the error
                clk.accumulatedTimingError += timeInterval[0]-t
                # tare the clock and delay the proper amount
                clk.tare(timeInterval[0])
                clk.delay(soundClip.getDuration())

	    # it would be great if the soundClip knew the formatsize...
	    if appended < self.total_samples:
		# mark the offset into the sound clip
		self.startInd = appended*self.eplsound.FORMAT_SIZE
		self.endInd = len(soundClip.snd) #self.total_samples*self.eplsound.FORMAT_SIZE

		# Add the callback to continue playing
		self.last_play = timeInterval[0]
		addPollCallback(self.__playCallback__, soundClip.snd, 0, ampFactor)
		
            dur = soundClip.getDuration()

        else:
            dur = 0
            timeInterval = (t,0)
            
        # log message        
        self.logMessage("%s\t%s\t%s" % ("P",shortName,dur), timeInterval)

        return timeInterval

    def __playCallback__(self, s, ow, ampFactor):
	"""
	Timer for appending the remainder of a sound.
	"""
    	currentTime = timing.now()

    	if self.playing and currentTime >= self.last_play + self.play_interval:
	    # see if stop the time
	    if self.startInd < self.endInd:

		# determine how much to append
		actualInd = self.startInd + self.bytes_per_append

		# make sure it's not beyond the end
		if actualInd > self.endInd:
		    # just set to the end
		    actualInd = self.endInd
		
		# append the sound
		appended = self.eplsound.append(s[self.startInd:actualInd],
                                                len(s[self.startInd:actualInd])/self.eplsound.FORMAT_SIZE, 0, ampFactor)

		self.last_play = currentTime
		
		# update the startInd
		if appended > 0:
		    self.startInd += appended*self.eplsound.FORMAT_SIZE
		
	    else:
		# no more sound
		if (self.eplsound.getSamplesPlayed()*self.eplsound.NUM_CHANNELS)>=self.total_samples:
		    self.playStop()

    def playLoopStop(self, doUnload=True):
        self.playStop(doUnload)

    def playStop(self, doUnload=True):
	if self.playing:
	    self.playing = False
	    removePollCallback(self.__playCallback__)           
	    removePollCallback(self.__playLoopCallback__)           
        
        # clear the sound buffer to stop playing
	self.eplsound.clearPlayBuffer()

	if isinstance(self.currentClip, FileAudioClip) and self.currentClip.isLoaded() and doUnload:
	    self.currentClip.unload()
	    

	return self.eplsound.getSamplesPlayed()


    def playLoop(self, soundClip, t = None, ampFactor=1.0, doDelay=True):
        """
        Play an AudioClip and return the time and latency of when the
        sound played.

        INPUT ARGS:
          soundClip- AudioClip object of the sound to be played
          t- Optional PresentationClock for timing.
          ampFactor- Optional amplification of sound.  (default value is 1)
          doDelay- Optionally do not tare and move the presentation clock
            forward.  Defaults to True (moving the clock forward)
          
        OUTPUT ARGS:
          timestamp- time and latency when sound playing began.
          
        """          

	# Must be sure to not get multiple callbacks at once, so
	# playing a soundclip while another is running causes that 
	# other one to stop immediately, even if it is not done playing.
	# self.playStop()

	# handle special case: if it's a FileAudioClip and needs loading,
	# load it.
	self.currentClip = soundClip
        if isinstance(soundClip, FileAudioClip):
	    if not soundClip.isLoaded():
		# load and append the sound
		soundClip.load()
	    # for logging
	    shortName = soundClip.filename
	else:
	    shortName = "NOFILE"

        if isinstance(t, exputils.PresentationClock):
            clk = t
	else:
	    clk = exputils.PresentationClock()
	
	t = clk.get()

        if not soundClip.snd is None:
	    # first, compute how many bytes our initial chunk
	    # to append is. ASSUMPTION: always starting from byte 0.
	    firstbytes = min(self.bytes_per_append, len(soundClip.snd))
	    self.total_samples = int(math.floor(len(soundClip.snd)/self.eplsound.FORMAT_SIZE))

	    if self.playing:
		# stop the playing sound 5ms prior to the new time
		timing.timedCall(t-5, self.playStop, False)
	    self.playing = True
	    self.eplsound.resetSamplesPlayed()
	    (timeInterval, appended) = timing.timedCall(t,
						       self.eplsound.append,
						       soundClip.snd[0:firstbytes],
						       len(soundClip.snd[0:firstbytes])/self.eplsound.FORMAT_SIZE,
						       0, ampFactor)
    
            if doDelay:
                # accumulate the error
                clk.accumulatedTimingError += timeInterval[0]-t
                # tare the clock and delay the proper amount
                clk.tare(timeInterval[0])
                clk.delay(soundClip.getDuration())

	    # it would be great if the soundClip knew the formatsize...
	    # mark the offset into the sound clip
            self.startInd = appended*self.eplsound.FORMAT_SIZE
            self.endInd = len(soundClip.snd) #self.total_samples*self.eplsound.FORMAT_SIZE

            # Add the callback to continue playing
            self.last_play = timeInterval[0]
            #addPollCallback(self.__playLoopCallback__, soundClip.snd, 0, ampFactor)
            addPollCallback(self.__playLoopCallback__, 0, ampFactor)
		
            dur = soundClip.getDuration()

        else:
            dur = 0
            
        # log message        
        self.logMessage("%s\t%s\t%s" % ("P",shortName,dur), timeInterval)

        return timeInterval

    def __playLoopCallback__(self, ow, ampFactor):
	"""
	Timer for appending the remainder of a sound.
	"""
    	currentTime = timing.now()

    	if self.playing and currentTime >= self.last_play + self.play_interval:
	    # see if stop the time
	    if self.startInd < self.endInd:
                # do the sound
                s = self.currentClip.snd

		# determine how much to append
                toplay = self.eplsound.getBufferUsed()
                toappend = self.bytes_per_append - toplay
                if toappend <= 0:
                    return
                
                actualInd = self.startInd + toappend  # self.bytes_per_append

		# make sure it's not beyond the end
		if actualInd > self.endInd:
		    # just set to the end
		    actualInd = self.endInd
		
		# append the sound
		appended = self.eplsound.append(s[self.startInd:actualInd], len(s[self.startInd:actualInd])/self.eplsound.FORMAT_SIZE, 0, ampFactor)

                self.last_play = currentTime
		
		# update the startInd
		if appended > 0:
		    self.startInd += appended*self.eplsound.FORMAT_SIZE
		
	    else:
		# no more sound, so start again right away
                self.startInd = 0


        
    def startRecording(self, basename = None, t = None, **sfargs):
        """
        Starts recording and returns a tuple of the AudioClip and the time
        of recording onset.

        INPUT ARGS:
          t- optional PresentationClock for timing.
	  sfargs- keyword arguments for FileAudioClip constructor

        OUTPUT ARGS:
          recClip- The AudioClip object that will contain the recorded data.
          timestamp- time and latency when sound recording began.
        """
        if not self.recording:
            # get a new audio clip to record to
	    if not basename is None:
		# send output to file
		self.recClip = FileAudioClip(self.archive, basename, **sfargs)
	    else:
		# record in memory
		if len(sfargs)>0:
		    raise SoundException("Cannot pass sfargs to AudioClip constructor; you must be recording to file.")
		self.recClip = AudioClip()

            # start recording
            if isinstance(t, exputils.PresentationClock):
                t = t.get()
            (timeInterval,val) = timing.timedCall(t, self.eplsound.recstart)
            
            # Add the callback to continue recording
            self.recording = True
            self.last_rec = timeInterval[0]
            addPollCallback(self.__recCallback__)
            
            # log message
	    if basename:
		shortName = self.recClip.filename
	    else:
		shortName = "NOFILE"
            self.logMessage("%s\t%s" % ("RB",shortName),timeInterval)
            
            return (self.recClip,timeInterval)

    def flush(self):
        """
        Flush the recording buffer.
        """
        currentTime = timing.now()
        newstuff = self.getBuffData()

        # Update the last time
        self.last_rec = currentTime

        if len(newstuff) > 0:
            # append the data to the clip
            self.recClip.append(newstuff, self.eplsound.getRecChans())        
        

    def __recCallback__(self):
        """
        Internal callback function, only for use by pyEpl functions.
        Thread function for recording, called by startRecording.
        """
        currentTime = timing.now()
        if self.recording and currentTime >= self.last_rec + self.rec_interval:
	    newstuff = self.getBuffData()

            # Update the last time
            self.last_rec = currentTime

            if len(newstuff) > 0:
                # append the data to the clip
                self.recClip.append(newstuff, self.eplsound.getRecChans())        
      
    def getBuffData(self):
	# allocate a buffer of appropriate length
	bufflen = self.eplsound.REC_BUF_LEN*self.eplsound.getSampleRate()*self.eplsound.getRecChans()
	buff = ' '*bufflen*self.eplsound.FORMAT_SIZE

	# use it to receive recorded data
	consumed = self.eplsound.consume(buff, bufflen)
	return buff[0:consumed*self.eplsound.FORMAT_SIZE]
	
    def stopRecording(self, t = None):
        """
        Stops recording and returns the resulting audio clip and the time
        recording ended.

        INPUT ARGS:
          t- optional PresentationClock for timing.

        OUTPUT ARGS:
          recClip- The AudioClip object that contains the recorded data.
          timestamp- time and latency when sound recording ended.
          
        """
        if self.recording:
            # stop recording
            if isinstance(t, exputils.PresentationClock):
                t = t.get()
            (timeInterval,val) = timing.timedCall(t, self.eplsound.recstop)

            # Remove the recording callback
            self.recording = False
            removePollCallback(self.__recCallback__)
            
            # get the rest of the data from recbuffer
	    newstuff = self.getBuffData()

            if len(newstuff) > 0:
                # append the data to the clip
                self.recClip.append(newstuff, self.eplsound.getRecChans())            

            # log message
	    if isinstance(self.recClip, FileAudioClip):
		shortName = self.recClip.filename
	    else:
		shortName = "NOFILE"
            self.logMessage("%s\t%s" % ("RE", shortName), timeInterval)
            
            r = self.recClip
            del self.recClip
            return (r, timeInterval)

    def record(self, duration, basename = None, t = None, **sfargs):
        """
        Perform a blocked recording for a specified duration (in milliseconds).

        INPUT ARGS:
          duration- length of time (in ms.) to record for.
          basename- filename to save recorded data to.
          t- optional PresentationClock for timing.
	  sfargs- keyword arguments passed to FileAudioClip constructor

        OUTPUT ARGS:
          recClip- The AudioClip object that contains the recorded data.
          timestamp- time and latency when sound recording began.
        """
        if not t:
            t = timing.now()
        elif isinstance(t, exputils.PresentationClock):
            clk = t
            t = clk.get()
            clk.delay(duration)
        (r,starttime) = self.startRecording(basename, t = t, **sfargs)
        (r,stoptime) = self.stopRecording(t = t + duration)
        return (r,starttime)

    def combineClips(self,clips):
        """
        Combine a list of AudioClips together, aligning to the beginning of both
        and returning a clip the length of the longer clip.
        """

        # start with None
        base = None

        for clipinfo in clips:
            # split out the info
            if isinstance(clipinfo,tuple):
                clip = clipinfo[0]
                clipOffset = clipinfo[1]
            else:
                clip = clipinfo
                clipOffset = 0

            # convert from str to numpy array
            toadd = clip.stripChannel(clip.snd)
            toadd = numpy.array(struct.unpack(str(len(toadd)/clip.sampleWidth) + 'h', toadd), dtype=numpy.int64)

            # add in on beginning if necessary
            if clipOffset > 0:
                toadd = numpy.concatenate([numpy.zeros(clipOffset),toadd])

            if base is None:
                base = toadd
            else:
                # see the diff in length
                clipdiff = len(base) - len(toadd)

                if clipdiff > 0:
                    # append zeros to the clip
                    toadd = numpy.concatenate([toadd,numpy.zeros(clipdiff)])
                elif clipdiff < 0:
                    # append zeros to the base
                    base = numpy.concatenate([base,numpy.zeros(-clipdiff)])

                # add the new signal
                base = base + toadd

        # normalize the clips to the max
        maxval = numpy.abs(base).max()
        if maxval > self.eplsound.SCALE:
            base = base * self.eplsound.SCALE / maxval

        # convert back to int16
        base = base.astype(numpy.int16)

        return AudioClip(clips[0].duplicateChannel(base))


