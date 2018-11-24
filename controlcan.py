#!/usr/bin/env python3
from ctypes import *

VCI_USBCAN2A = 4

class ControlCAN:
    def __init__(self, device_type=VCI_USBCAN2A, library='ControlCAN.dll'):
        self.dll = windll.LoadLibrary(library)