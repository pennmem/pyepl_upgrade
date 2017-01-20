# PyEPL: hardware/sound/testsound.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

import sound
import time
import Numeric
import struct

secs = 5
formatsize = 2

sound.init(60,2)

print "Recording for %d seconds..." % secs
sound.recstart()
time.sleep(secs)
sound.recstop()


s = sound.consume(secs*44100*2)

# duplicate it
print sound.getRecChans()

if sound.getRecChans() == 1:
   buff = Numeric.array(struct.unpack(str(len(s)/formatsize) + 'h', s),typecode=Numeric.Int16)
   xbuff = Numeric.zeros((len(buff)*2),typecode=Numeric.Int16)
   xbuff[::2] = buff;
   xbuff[1::2] = buff;

   # convert to a string
   s = str(buffer(xbuff))

   # clean up
   del xbuff
   del buff


print len(s)
for i in range(5):
   print "Playing sound"
   sound.playStart(s,0,1)
   time.sleep(secs)


sound.deinit()



