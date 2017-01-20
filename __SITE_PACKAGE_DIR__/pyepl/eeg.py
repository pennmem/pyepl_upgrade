# PyEPL: eeg.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides EEG sync pulsing and logging.
"""
from textlog import LogTrack
from hardware import addPollCallback, removePollCallback, EPLPulseEEGException
import timing
import exceptions
import exputils

# import python modules
import random
import sys

class EEGTrackRefManager:
    def __init__(self, f):
        self.__call__ = f

class EEGTrack(LogTrack):
    """
    This track recognizes if you are sending sync pulses via USB or
    through a parallel port or if you are connected directly to the
    data access (Like in the RTLinux scalp EEG setup) and
    automatically starts sending pulses and logging the times of the
    pulses.
    """
    logExtension = ".eeglog"
    def __init__(self, basename, archive = None, autoStart = True):
        """
        Set up the EEGTrack.

        INPUT ARGS:
          basename- The name of the log.
          archive- Directory to put the log.
          autoStart- Whether to automatically start the service
                     and logging.
        """
        self.eeg_files = []
        self.record_mode = "N" # N: neither, S: scalp, P: pulse
        self.do_log = False
        self.dat_file = None
        self.EEG_sync_thread = None
        self.awCard = None
        self.labjack = None
        self.boardType = None

        if not archive:
            self.archive = exputils.session
        else:
            self.archive = archive
        
        LogTrack.__init__(self, basename, archive, autoStart)

        
    def startService(self):
        """
        Start the EEG service, testing what type of synching to do and
        opening ports as necessary.
        """
        # If Darwin, then only check pulse
        if sys.platform == 'darwin':
            # see if can open Pulse port
            try:
                from hardware import LJCard
                self.labjack = LJCard()
                self.boardType = 'LJ'
                if self.labjack.isAutoStimVer():
                    self.boardType = 'LJ_autostim'
                self.record_mode = "P"
            except:
                # both failed so neither
                # report / raise something
                self.record_mode = "N"
                exceptions.eplWarn("Neither Scalp nor Pulse EEG syncing was initialized.")
        else:        
            # import eeg stuph
            from hardware import Parallel, EEGShmAttached, EEGShmAttach, \
            EEGShmDetach, EEGRecStart, EEGRecStop, EEGGetOffset, EPLScalpEEGException

            # see if can attach to shared memory
            try:
                EEGShmAttach()
                self.record_mode = "S"
            except EPLScalpEEGException:
                # did not attach
                # see if can open Pulse port
                try:
                    self.parallel = Parallel()
                    self.record_mode = "P"
                except:
                    # both failed so neither
                    # report / raise something
                    self.record_mode = "N"
                    exceptions.eplWarn("Neither Scalp nor Pulse EEG syncing was initialized.")

                
    def stopService(self):
        """
        Stop the EEG syncing.
        """
        # clean up
        if self.record_mode == "S":
            EEGRecStop()
            EEGShmDetach()
        elif self.record_mode == "P":
            if self.awCard: # on darwin
                del self.awCard
            elif self.labjack:
                self.labjack.setAllLow()
                del self.labjack
            else: 
                del self.parallel

    def startLogging(self):
        """
        Start sending synchs and logging.
        """
        # start logging
        LogTrack.startLogging(self)
        
        # check record state, maybe get new file, start recording
        if self.record_mode == "S":
            # is scalp, so start recording to new file
            self.dat_filename = 'eeg0.dat'
            
            # make sure we have a file name that doesn't already exist...
            n = 0
            while self.archive.exists(self.dat_filename):
                n += 1
                self.dat_filename = 'eeg%d.dat' % n
            self.dat_file = self.archive.createFile(self.dat_filename)
            self.dat_file.close()
            EEGRecStart(self.dat_file.name)

            # setup scalp callback
            self.last_align = timing.now()
            self.align_interval = 1000
            addPollCallback(self.scalpCallback)
            
        elif self.record_mode == "P":
            # is pulse, so setup pulse callback
            self.last_align = timing.now()
            self.align_interval = 1000
            self.pulseTrain(10,"EXPSTART_")
            addPollCallback(self.pulseCallback)

    def newTarget(self, archive):
        """
        Switch to a new archive location for this EEG log.
        """
        # first update the archive that will be used for the EEG data file
        self.archive = archive
        LogTrack.newTarget(self, archive)
            
    def stopLogging(self):
        """
        Stop sending syncs and logging them.
        """
        # clean up recording
        # stop logging/ remove callbacks
        removePollCallback(self.scalpCallback)
        removePollCallback(self.pulseCallback)
        
        if self.record_mode == "S":
            # stop recording
            EEGRecStop()
            
        elif self.record_mode == "P":
            self.pulseTrain(5,"EXPEND_")

        # stop logging
        LogTrack.stopLogging(self)


    def scalpCallback(self):
        """
        Callback to make logs using the real-time scalp interface.
        """
        # is it time to do another alignment?
        if timing.now() >= self.last_align + self.align_interval:
            # query for offset
            (timeInterval,offset) = timing.timedCall(None,
                                                     EEGGetOffset)
            # get info for log message
            self.logMessage("%s\t%s" % (self.dat_filename,offset),timeInterval) 
            
            # update last_align
            self.last_align = timeInterval[0]

    def timedStim(self, duration, freq, doRelay=False):
        '''
        Start a sync box controlled train of pulses to trigger a stimulator.
        
        INPUT ARGS:
          duration - duration of stimulation (s)
          freq - frequency to send pulse (Hz)
        '''
        
        # use the current time
        clk = timing.now()
        
        # only labjack boxes support stimulation
        if self.labjack:
            (timeInterval,returnValue)=timing.timedCall(clk, self.labjack.StartStim, duration, freq, doRelay)
                
            # log start of stimulation
            self.logMessage("STIM_ON",timeInterval)
            return timeInterval
        else:
            raise EPLPulseEEGException("timedStim only functions with labjack autostim boards.")
        
    def timedPulse(self, pulseTime, pulsePrefix='', signal='', clk=None, output_channel=0):
        """
        Send a pulse and log it.

        INPUT ARGS:
          pulseTime- Duration of pulse.
          pulsePrefix- Name to log the pulse.
        """
        # see if using clock
        usingClock = True
        if clk is None:
            # no clock, so use time
            clk = timing.now()
            usingClock = False

        if self.awCard:
            if len(signal)>0:
                (timeInterval,returnValue)=timing.timedCall(clk, self.awCard.write, signal)
            else:
                (timeInterval,returnValue)=timing.timedCall(clk, self.awCard.allOn)
        elif self.labjack:
            (timeInterval,returnValue)=timing.timedCall(clk, self.labjack.setFIOState, output_channel, 0 if output_channel==4 else 1)
            pulsePrefix = "CHANNEL_" + str(output_channel) + "_"
        else:
            if len(signal)>0:
                (timeInterval,returnValue)=timing.timedCall(clk, self.parallel.setSignal, True, signal)
            else:
                (timeInterval,returnValue)=timing.timedCall(clk, self.parallel.setState, True)
        self.logMessage("%s" %  pulsePrefix+"UP",timeInterval)

        # wait for the pulse time
        if usingClock:
            clk.delay(pulseTime)
        else:
            clk = clk + pulseTime

        if self.awCard:
            (timeInterval,returnValue)=timing.timedCall(clk, self.awCard.allOff)
        elif self.labjack:
            (timeInterval,returnValue)=timing.timedCall(clk, self.labjack.setFIOState, output_channel, 1 if output_channel==4 else 0)
        else:
            (timeInterval,returnValue)=timing.timedCall(clk, self.parallel.setState, False)

        self.logMessage("%s" %  pulsePrefix+"DN",timeInterval)

        # I'm not sure when if you want this to be the start or end of the pulse
        return timeInterval
        
    def pulseTrain(self, numPulses,trainName=""):
        """
        Send a train of pulses.

        INPUT ARGS:
          numPulses- Number of pulses in train.
          trainName- Name to use in the log.
        """
        #trainLen denotes the number of pulses in this train
        pulseLen=10 #in milliseconds
        interPulseInterval=5

        self.logMessage(trainName+"TRAIN")
        
        # set the desired pulsetime
        pulseTime = timing.now()
        for i in range(numPulses):
            # send a pulse
            (timeInterval,returnValue)=timing.timedCall(pulseTime,
                                                        self.timedPulse, 
                                                        pulseLen,'TRAIN_')
            # pause for the next pulse
            pulseTime += interPulseInterval

    def configFreq(self, frequency):
        """
        Configures stimulation so that stimulation trains can happen
        more quickly
         
        NOTE: ONLY FUNCTIONS ON TTL2

        INPUT ARGS:
            frequency - the frequency (Hz) at which to configure

        """
        
        # Log the frequency
        self.logMessage("CONFIG\t%d"%frequency)
        
        # Set the time at which to configure
        configTime = timing.now()
        if not self.labjack:
            raise(Exception('CAN ONLY CONFIGURE FREQUENCY ON LABJACK'))
        (timeInterval, returnValue)=timing.timedCall(configTime,\
                self.labjack.configFreq,\
                frequency)
        return timeInterval

    def sendFreq(self, duration, freqhz, duration_is_cycles = False):
        """
        Sends a train of pulses at a given frequency on TTL2
        NOTE: MUST CALL configFreq FIRST TO GET ACCURATE RESULTS

        INPUT ARGS:
            duration - Duration of the train (defaults to seconds,
                       can override with 3rd argument)
            freqhz   - Frequency at which to stimulate in Hz
            duration_is_cycles - Whether duration provided is 
                                 in seconds or number of pulses
                                 (default: False)
        """
    
        if not self.labjack:
            raise(Exception('CAN ONLY USE THIS FUNCTION ON LABJACK'))

        # Time at which to send the pulse
        trainTime = timing.now()
        (timeInterval, returnValue) = timing.timedCall(\
                trainTime,\
                self.labjack.pulseTrain,\
                duration,\
                freqhz,\
                duration_is_cycles)

        if duration_is_cycles:
            self.logMessage('STIM_TRAIN\t%d\t%d'%(int(round(float(duration)/freqhz)), freqhz), timeInterval)
        else:
            self.logMessage('STIM_TRAIN\t%d\t%d'%(duration, freqhz), timeInterval)
    
        return timeInterval




    def pulseCallback(self):
        """
        Callback to manage sending pulses.
        """
        minInterPulsetime=750
        maxInterPulseTime=1250
        pulseLen=10 #in milliseconds        
        if timing.now() >= self.last_align + self.align_interval:
            timeInterval = self.timedPulse(pulseLen)

            # randomize the alignment interval
            self.align_interval = random.uniform(minInterPulsetime, maxInterPulseTime)

            # update last_align
            self.last_align = timeInterval[0]


    def calcOffset(eventTime):
        """
        Return a two tuple of the offset in to the file and a maximum latency value.
        The offset into the file is a string representation of "FILENAME\tOffset".
        The maximum latency is simply a number in ms.
        """
        # keep the last
        startTime = None
        endTime = None
        for (timeStamp,withinTick,logMessage) in self:
            if timeStamp[0] >= eventTime[0]:
                # we have passed the time
                endTime = timeStamp
                endLog = logMessage
                break
            else:
                # save as last time
                startTime = timeStamp
                startLog = logMessage

        # set defaults
        filename = ""
        offset = ""
        ml = 0

        # see if found
        if startTime is not None and endTime is not None:
            # get the filenames and offsets
            [startFile,startOffset] = startLog.split('\t')
            [endFile,endOffset] = startLog.split('\t')

            if startFile == endFile:
                filename = startFile

                # calc the slope
                slope = float(endOffset - startOffset)/float(endTime[0] - startTime[0])

                # calc the offset
                offset = (slope * (eventTime[0] - startTime[0]) + startOffset)
            
                # eventually, we'll add in a maximum latency in the offset
                # using the ml values from the start and end times.  Thus,
                # we'll calculate four lines, return the min value as the
                # offset and the max-min as the latency in samples

        # return what we gots
        return ("%s\t%s" % (filename,offset),ml)


    def clientPulse(self, pulseTime, clk=None):
        """
        Do a blocking timed pulse on channel 2, specially designated
        for pulses from experiment code.
        """
        if self.labjack==None:
            raise EPLPulseEEGException("Client pulse methods are only callable with multiple outputs.")
        self.timedPulse(pulseTime, '', '', clk, 1)

    def clientHighNow(self, clk=None):
        """
        Do a non-blocking high on channel 2.
        """
        if self.labjack==None:
            raise EPLPulseEEGException("Client pulse methods are only callable with multiple outputs.")
        if clk is None:
            # no clock, so use time
            clk = timing.now()
        (timeInterval,returnValue)=timing.timedCall(clk, self.labjack.setChannel2Hi)
        pulsePrefix = "CHANNEL_2_"
        self.logMessage("%s" %  pulsePrefix+"UP",timeInterval)

    def clientLowNow(self, clk=None):        
        """
        Do a non-blocking low on channel 2
        """
        if self.labjack==None:
            raise EPLPulseEEGException("Client pulse methods are only callable with multiple outputs.")
        if clk is None:
            # no clock, so use time
            clk = timing.now()
        (timeInterval,returnValue)=timing.timedCall(clk, self.labjack.setChannel2Low)
        pulsePrefix = "CHANNEL_2_"
        self.logMessage("%s" %  pulsePrefix+"DN",timeInterval)

    def getReference():
        return self

    getReference = EEGTrackRefManager(getReference)
