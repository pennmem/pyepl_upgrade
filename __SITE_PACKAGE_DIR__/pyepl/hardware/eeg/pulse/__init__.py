# PyEPL: hardware/eeg/pulse/__init__.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

import sys
from pulseexc import EPLPulseEEGException
if sys.platform=='darwin':
    #from awCard import awCard, AWCException
    import u3
else:
    from parallel import Parallel

class LabJack(u3.U3):
    """
    Adds some convenience functions to the built-in U3 methods
    """
    def __init__(self):
        u3.U3.__init__(self)

        # check which version of the labjack board
        # if state is 0, then it is the version with automatic stim
        # on TTL 2
        state = self.isAutoStimVer()
        self.chanTTL2 = 1
        if state:
            self.chanTTL2 = 4
            print 'Labjack AutoStim board connected'
        else:
            print "Labjack board connected."

        self.setAllLow()
       
        self.timer_val = 250

        self.clockBases = \
                {3:1000000,\
                 4:4000000,\
                 5:12000000,\
                 6:48000000}

        self.tc_base = 3

    def setAllLow(self):
        self.setFIOState(0, 0)
        self.setFIOState(2, 0)
        self.setFIOState(3, 0)
        self.setFIOState(self.chanTTL2, 1)

    def setAllHi(self):
        self.setFIOState(0, 1)
        self.setFIOState(2, 1)
        self.setFIOState(3, 1)
        self.setFIOState(self.chanTTL2, 0)
           
    def setChannel1Hi(self):
        self.setFIOState(0, 1)

    def setChannel2Hi(self):
        self.setFIOState(self.chanTTL2, 0)

    def setChannel1Low(self):
        self.setFIOState(0, 0)

    def setChannel2Low(self):
        self.setFIOState(self.chanTTL2, 1)

    def setRelay1On(self):
        self.setFIOState(2, 1)

    def setRelay2On(self):
        self.setFIOState(3, 1)

    def setRelay1Off(self):
        self.setFIOState(2, 0)

    def setRelay2Off(self):
        self.setFIOState(3, 0)

    def isAutoStimVer(self):
        return self.getFIOState(7) == 0        

    def StartStim(self,duration,freqhz,doRelay = False):

        if doRelay:
            print 'doing relay'
            self.setRelay1On()
            sleep(.3)
            self.setRelay1Off()


        # print ''
        # print 'Duration       = ', duration
        # print 'Frequency      = ', freqhz, 
        # print ''


        divisor     = int(250)
        clock_rate  = 1000000/divisor
        timer_val   = int(.5 * clock_rate / freqhz)
        num_cycles  = int(round(duration * freqhz))

        # Set the timer clock base and divisor

        tc_base     = 3; #48Mhz Clock

        # print ''
        # print 'TimerClockBase = ', tc_base
        # print 'Divisor        = ', divisor
        # print 'clock_rate     = ', clock_rate
        # print 'num_cycles     = ', num_cycles 
        # print 'timer_val      = ', timer_val
        # print ''

        
        # Only Allow 7.8125 Hz to 50 Hz

        if freqhz < 7.8125:
            print 'freqhz Out of Range, Must be within 7.8125 and 50 Hz'            
            sys.exit(0)

        #if freqhz > 50:
        #    print 'freqhz Out of Range, Must be within 7.8125 and 50 Hz'            
        #    sys.exit(0)

        # Only allow a certain range of duration

        #if duration < .1:
        #    print 'Duration Out of Range, Must be between .1 and 20 seconds'            
        #    sys.exit(0)

        #if duration > 5:
        #    print 'Duration Out of Range, Must be between .1 and 5 seconds'            
        #    sys.exit(0)

        # Set the timer/counter pin offset to 4, which will put the first
        # timer/counter on FIO4 and the second on FIO5.

        self.configIO(TimerCounterPinOffset = 4, EnableCounter1 = True, EnableCounter0 = None, NumberOfTimersEnabled = 2, FIOAnalog = None, EIOAnalog = None, EnableUART = None)
                       
        # Run at slower speed during debug, so LED flashing can be seen
        # Since we are using clock with divisor support, Counter0 is not available.

        # Set the timer base 
        self.configTimerClock( TimerClockBase = tc_base, TimerClockDivisor = divisor)
                
        # Configure timer1 for the number of pulses before stopping timer0
        timer_num   = 1
        mode        = 9
        self.writeRegister(7100+(2*timer_num), [mode, num_cycles])

        # Configure timer0 for frequency mode
        timer_num   = 0
        mode        = 7
        self.writeRegister(7100+(2*timer_num), [mode, timer_val])


    def configFreq(self, freqhz):
        """
        Configures the labjack so that you can simple call
        runFreq and it will send out a train of pulses at that
        frequency
        """

        # Set the timer clock base and divisor
        #b000: 4 MHz	
        #b001: 12 MHz	
        #b010: 48 MHz (Default)	
        #b011: 1 MHz/Divisor	
        #b100: 4 MHz/Divisor	
        #b101: 12 MHz/Divisor	
        #b110: 48 MHz/Divisor
        
        if freqhz<7.8125:
            print 'freqhz out of range. Must be above 7.8125'
            sys.exit(0)

        divisor = .5*float(self.clockBases[self.tc_base])/float(self.timer_val*freqhz)

        divisor = int(divisor)
        # Set the timer/counter pin offset to 4, which will put the first
        # timer/counter on FIO4 and the second on FIO5.
        self.configIO(TimerCounterPinOffset=4,\
                EnableCounter1 = True,\
                EnableCounter0 = None,\
                NumberOfTimersEnabled = 2,\
                FIOAnalog = None,\
                EIOAnalog = None,\
                EnableUART = None)
            
        # Set the timer base 
        self.configTimerClock( TimerClockBase = self.tc_base, TimerClockDivisor = divisor) 

    def pulseTrain(self, duration, freqhz, duration_is_cycles=False):
        if not duration_is_cycles:
            num_cycles = int(round(duration*freqhz))
        else:
            num_cycles = duration
        
        if freqhz<7.8125:
            print 'freqhz out of range. Must be above 7.8125'
            sys.exit(0)
        
        # Configure timer1 for the number of pulses before stopping timer0
        timer_num = 1
        mode = 9
        self.writeRegister(7100+(2*timer_num), [mode, num_cycles])

        # Configure timer0 for frequency mode
        timer_num   = 0
        mode        = 7
        self.writeRegister(7100+(2*timer_num), [mode, self.timer_val])

