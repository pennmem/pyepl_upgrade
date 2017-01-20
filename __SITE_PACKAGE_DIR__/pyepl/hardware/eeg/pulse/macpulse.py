# PyEPL: hardware/eeg/pulse/macpulse.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
Sends out synch pulses via the ActiveWire USB device for macs only.
"""

from pulseexc import EPLPulseEEGException
import objc    

board=None

def initialize(**options):
    pass

def finalize():
    pass

def openPort():
    global board
    objc.loadBundle('ActiveWireBoard',globals(),bundle_path='/Library/Frameworks/ActiveWireBoard.framework');

    board=ActiveWireBoard.alloc()
    board.init()
    if board.openBoard()==False:
        print 'error opening board'
        raise EPLPulseEEGException("Couldn't open ActiveWire Board")

    if board.setBinaryPinDirections_("1111111111111111") == False:
        raise EPLPulseEEGException("Couldn't set pin directions")
    setState(False) #force the board to always start low
    
def closePort():
    global board
    board.closeBoard()
    board=None

def setState(state):
    global board
    if state:
        ret=board.writeBinaryData_length_("1111111111111111",2)
    else:
        ret=board.writeBinaryData_length_("0000000000000000",2)

    if not ret:
        raise EPLPulseEEGException("Error writing to the Activewireboard")

def setSignal(state, signal):
    global board
    if state:
        ret=board.writeBinaryData_length_(signal, 2)
    else:
        ret=board.writeBinaryData_length_("0000000000000000",2)

    if not ret:
        raise EPLPulseEEGException("Error writing to the Activewireboard")
