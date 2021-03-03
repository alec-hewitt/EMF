from ctypes import *
import time
from dwfconstants import *
import sys

class Digilent:

    def __init__(self):
        #Load DWF Library
        self.dwf = cdll.LoadLibrary("libdwf.so")
        self.hdwf = c_int()
        self.channel = c_int(0)

        version = create_string_buffer(16)
        self.dwf.FDwfGetVersion(version)
        print("DWF Version: "+str(version.value))

        self.dwf.FDwfParamSet(DwfParamOnClose, c_int(0)) # 0 = run, 1 = stop, 2 = shutdown

    def findSignalVoltage(self, EMF):
        return 0.0665*EMF

    def open(self):
        #open device
        print("Opening Digilent")
        self.dwf.FDwfDeviceOpen(c_int(-1), byref(self.hdwf))

        if self.hdwf.value == hdwfNone.value:
            print("failed to open Digilent")
            return 1
        else:
            return 0

        self.dwf.FDwfDeviceAutoConfigureSet(self.hdwf, c_int(0)) # 0 = the device will be configured only when calling FDwf###Configure

    def sine_out(self, freq, amp):

        self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, self.channel, AnalogOutNodeCarrier, c_bool(True))
        self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, self.channel, AnalogOutNodeCarrier, funcSine)
        self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, self.channel, AnalogOutNodeCarrier, c_double(freq))
        self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, self.channel, AnalogOutNodeCarrier, c_double(amp))
        #self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, self.channel, AnalogOutNodeCarrier, c_double(amp))
        print("Generating sine wave..")
        self.dwf.FDwfAnalogOutConfigure(self.hdwf, self.channel, c_bool(True))

    #configures the analog aquisition with sample size and rate
    def configure_aquisition(self, nSamples, acqFreq):
        self.dfw.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
        self.dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(5)) #TODO: Change this channel range to be based on the signal output & amplifier gain
        self.dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeRecord)

    #def sample_analog(self):

    def disable_analog(self):
        print("Disabling analog output")
        self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, self.channel, AnalogOutNodeCarrier, c_bool(False))

    def close(self):
        print("Terminating Discovery Connection")
        self.dwf.FDwfDeviceClose(self.hdwf)
