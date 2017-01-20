# PyEPL: calibration.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides a uniform way to calibrate devices which may
differ in performance across machines and over time.
"""

from repository import reposRoot

class Calibrator:
    """
    This is a super-class for classes designed to calibrate a certain
    type of device.
    """
    def __init__(self, name):
        """
        Initialize.
        """
        self.name = name
    def restoreCalibration(self):
        """
        Restore correctly calibrated hardware and software settings.
        """
        if self.isCalibrated():
            self.restore(reposRoot["calibration"][self.name]())
    def testCalibration(self):
        """
        Verify that the current settings are correct.
        """
        if not self.isCalibrated():
            return False
        return self.test(reposRoot["calibration"][self.name]())
    def calibrate(self):
        """
        Determine the correct calibration settings (perhaps
        interactively).
        """
        if not reposRoot.exists("calibration"):
            reposRoot["calibration"] = Directory()
        reposRoot["calibration"][self.name] = Wrap(self.cal())
    def isCalibrated(self):
        """
        Return True if a calibration has be stored for this device.
        Otherwise return False.
        """
        if not reposRoot.exists("calibration"):
            reposRoot["calibration"] = Directory()
            return False
        return reposRoot["calibration"].exists(self.name)
    # Methods to be overridden by inheritor:
    def restore(self, cal):
        """
        Restore calibration indicated by object cal.
        """
        pass
    def test(self, cal):
        """
        Test calibration indicated by object cal.
        """
        pass
    def cal(self):
        """
        Calibrate, return a picklable object that will be 'understood'
        by the restore and test methods.
        """
        pass
