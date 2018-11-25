#!/usr/bin/env python3
from ctypes import *
import logging


log = logging.getLogger("controlcan")

class VCI_INIT_CONFIG(Structure):
    """
    typedef struct _INIT_CONFIG{
        DWORD	AccCode;  // PID 子网
        DWORD	AccMask;  // PID 掩码
        DWORD	Reserved;
        UCHAR	Filter;  // 0/1 接收所有帧, 2: 只收标准帧, 3: 只收扩展帧
        UCHAR	Timing0; // BTR0 寄存器，指示波特率
        UCHAR	Timing1; // BTR1 寄存器，指示波特率
        UCHAR	Mode;
    }VCI_INIT_CONFIG,*PVCI_INIT_CONFIG;
    """
    _fields_ = [
        ("AccCode", c_ulong),
        ("AccMask", c_ulong),
        ("Reserved", c_ulong),
        ("Filter", c_ubyte),
        ("Timing0", c_ubyte),
        ("Timing1", c_ubyte),
        ("Mode", c_ubyte)
    ]

    FILTER_OFF = 0;
    FILTER_PRESERVE_ALL = 1;
    FILTER_PRESERVE_NORMAL = 2;
    FILTER_PRESERVE_EXT = 3;

    TIMING_REGS = {
        10: (0x31, 0x1C),
        20: (0x18, 0x1C),
        40: (0x87, 0xFF),
        50: (0x09, 0x1C),
        80: (0x83, 0xFF),
        100: (0x04, 0x1C),
        125: (0x03, 0x1C),
        200: (0x81, 0xFA),
        250: (0x01, 0x1C),
        400: (0x80, 0xFA),
        500: (0x00, 0x1C),
        666: (0x80, 0xB6),
        800: (0x00, 0x16),
        1000: (0x00, 0x14),
        33.33: (0x09, 0x6F),
        66.66: (0x04, 0x6F),
        83.33: (0x03, 0x6F),
    }

    MODE_NORMAL = 0;
    MODE_LISTEN = 1;
    MODE_LOOPBACK = 2;

    def __init__(self, pid=0x80000008, mask=0xffffffff,
                 filter_mode=FILTER_OFF,
                 baud=100,timing_regs=None, mode=MODE_NORMAL):
        if isinstance(timing_regs, tuple) and len(timing_regs) == 2:
            t0, t1 = timing_regs
        else:
            t0, t1 = self.TIMING_REGS[baud]
        return super().__init__(pid, mask, 0, filter_mode, t0, t1, mode)


class VCI_CAN_OBJ(Structure):
    """
    typedef  struct  _VCI_CAN_OBJ{
        UINT	ID; // 帧ID，标准帧11位，扩展帧29位
        UINT	TimeStamp; // 时间戳，发送帧无效
        BYTE	TimeFlag; // 为1时上面的时间戳有效。
        BYTE	SendType; // 为1时单次发送，不进行自动重发，文档建议为1
        BYTE	RemoteFlag; //是否是远程帧（数据段空）
        BYTE	ExternFlag; //是否是扩展帧（29位ID）
        BYTE	DataLen; // len<=8
        BYTE	Data[8]; // 8位buf
        BYTE	Reserved[3]; // 没用
    }VCI_CAN_OBJ,*PVCI_CAN_OBJ;
    """
    _fields_ = [
        ("ID", c_uint),
        ("TimeStamp", c_uint),
        ("TimeFlag", c_ubyte),
        ("SendType", c_ubyte),
        ("RemoteFlag", c_ubyte),
        ("ExternFlag", c_ubyte),
        ("DataLen", c_ubyte),
        ("Data", c_ubyte * 8),
        ("Reserved", c_ubyte * 3)
    ]
    _reserved_buf = (c_ubyte * 3)()

    def __init__(self, pid, data, timestamp=0, timeflag=0, sendtype=1, remoteflag=0, extended=0):
        assert isinstance(data, bytes) and len(data) <= 8, "VCI_CAN_OBJ only support byte array data under 8 bytes"

        log.debug(f"{self.__class__.__name__}.init {pid} {timestamp}"
            f"{timeflag} {sendtype} {remoteflag} {extended}"
            f"{len(data)} {data} {VCI_CAN_OBJ._reserved_buf}")
        return super().__init__(pid, timestamp,
            timeflag, sendtype, remoteflag, extended,
            len(data), (c_ubyte * 8)(*data), VCI_CAN_OBJ._reserved_buf)

PVCI_CAN_OBJ = POINTER(VCI_CAN_OBJ)

class VCI_BOARD_INFO(Structure):
    """
    typedef  struct  _VCI_BOARD_INFO{
		USHORT	hw_Version;
		USHORT	fw_Version;
		USHORT	dr_Version;
		USHORT	in_Version;
		USHORT	irq_Num;
		BYTE	can_Num;
		CHAR	str_Serial_Num[20];
		CHAR	str_hw_Type[40];
		USHORT	Reserved[4];
    } VCI_BOARD_INFO,*PVCI_BOARD_INFO;
    """
    _fields_ = [
		("hw_Version", c_ushort),
		("fw_Version", c_ushort),
		("dr_Version", c_ushort),
		("in_Version", c_ushort),
		("irq_Num", c_ushort),
		("can_Num", c_uint8),
		("str_Serial_Num", c_uint8 * 20),
		("str_hw_Type", c_uint8 * 40),
		("Reserved", c_ushort * 4),
    ]


class ControlCAN(object):
    TYPE_VCI_USBCAN1 = 3
    TYPE_VCI_USBCAN2 = 4
    TYPE_VCI_USBCAN2A = 4
    TYPE_VCI_USBCAN_E_U = 20
    TYPE_VCI_USBCAN_2E_U = 21

    def __init__(self, library='ControlCAN.dll', device_type=TYPE_VCI_USBCAN2, device_index=0):
        from pathlib import Path
        import sys

        if sys.platform == "win32":
            self._l = windll.LoadLibrary(str(Path(library).resolve()))
        elif sys.platform == "linux":
            self._l = cdll.LoadLibrary(str(Path(library).resolve()))
        else:
            raise NotImplementedError(f"ControlCAN not available on {sys.platform}!")

        if device_type != self.TYPE_VCI_USBCAN2:
            log.warning(f"device type {device_type} may not be supported")

        self.device_type = device_type
        self.device_index = device_index

        # Device Operation
        self._VCI_OpenDevice = self._l.VCI_OpenDevice
        self._VCI_OpenDevice.argtypes = (c_uint32, c_uint32, c_uint32)
        self._VCI_OpenDevice.restype = c_int32
        self._VCI_OpenDevice.errcheck = self._vci_errcheck()

        self._VCI_CloseDevice = self._l.VCI_CloseDevice
        self._VCI_CloseDevice.argtypes=(c_uint32, c_uint32)  # $1$3, DWORD DeviceInd)
        self._VCI_CloseDevice.restype = c_int32
        self._VCI_CloseDevice.errcheck = self._vci_errcheck()

        self._VCI_InitCAN = self._l.VCI_InitCAN
        self._VCI_InitCAN.argtypes=(c_uint32, c_uint32, c_uint32, POINTER(VCI_INIT_CONFIG))  # (DWORD DeviceType, DWORD DeviceInd, DWORD CANInd, PVCI_INIT_CONFIG pInitConfig)
        self._VCI_InitCAN.restype = c_int32
        self._VCI_InitCAN.errcheck = self._vci_errcheck()

        # Device info
        self._VCI_ReadBoardInfo = self._l.VCI_ReadBoardInfo
        self._VCI_ReadBoardInfo.argtypes=(c_uint32, c_uint32, POINTER(VCI_BOARD_INFO))  # (DWORD DeviceType, DWORD DeviceInd, PVCI_BOARD_INFO pInfo)
        self._VCI_ReadBoardInfo.restype = c_int32
        self._VCI_ReadBoardInfo.errcheck = self._vci_errcheck()

        # Baud rate
        self._VCI_SetReference = self._l.VCI_SetReference
        self._VCI_SetReference.argtypes=(c_uint32, c_uint32, c_uint32, c_uint32, c_void_p)  # (DWORD DeviceType, DWORD DeviceInd, DWORD CANInd, DWORD RefType, PVOID pData)
        self._VCI_SetReference.restype = c_int32
        self._VCI_SetReference.errcheck = self._vci_errcheck()

        # Buffer related
        self._VCI_GetReceiveNum = self._l.VCI_GetReceiveNum
        self._VCI_GetReceiveNum.argtypes=(c_uint32, c_uint32, c_uint32)  # (DWORD DeviceType, DWORD DeviceInd, DWORD CANInd)
        self._VCI_GetReceiveNum.restype = c_int32
        self._VCI_GetReceiveNum.errcheck = self._vci_errcheck()

        self._VCI_ClearBuffer = self._l.VCI_ClearBuffer
        self._VCI_ClearBuffer.argtypes=(c_uint32, c_uint32, c_uint32)  # (DWORD DeviceType, DWORD DeviceInd, DWORD CANInd)
        self._VCI_ClearBuffer.restype = c_int32
        self._VCI_ClearBuffer.errcheck = self._vci_errcheck()

        # CAN operation
        self._VCI_StartCAN = self._l.VCI_StartCAN
        self._VCI_StartCAN.argtypes=(c_uint32, c_uint32, c_uint32)  # (DWORD DeviceType, DWORD DeviceInd, DWORD CANInd)
        self._VCI_StartCAN.restype = c_int32
        self._VCI_StartCAN.errcheck = self._vci_errcheck()

        self._VCI_ResetCAN = self._l.VCI_ResetCAN
        self._VCI_ResetCAN.argtypes=(c_uint32, c_uint32, c_uint32)  # (DWORD DeviceType, DWORD DeviceInd, DWORD CANInd)
        self._VCI_ResetCAN.restype = c_int32
        self._VCI_ResetCAN.errcheck = self._vci_errcheck()

        # Data transmission
        self._VCI_Transmit = self._l.VCI_Transmit
        self._VCI_Transmit.argtypes=(c_uint32, c_uint32, c_uint32, PVCI_CAN_OBJ, c_ulong)  # (DWORD DeviceType, DWORD DeviceInd, DWORD CANInd, PVCI_CAN_OBJ pSend, ULONG Len)
        self._VCI_Transmit.restype = c_int32
        self._VCI_Transmit.errcheck = self._vci_errcheck()

        self._VCI_Receive = self._l.VCI_Receive
        self._VCI_Receive.argtypes=(c_uint32, c_uint32, c_uint32, PVCI_CAN_OBJ, c_ulong, c_int)  # (DWORD DeviceType, DWORD DeviceInd, DWORD CANInd, PVCI_CAN_OBJ pReceive, ULONG Len, INT WaitTime)
        self._VCI_Receive.restype = c_int32
        self._VCI_Receive.errcheck = self._vci_errcheck()

        # Device Reset
        # *NOT* ZLG Compatible!
        self._VCI_UsbDeviceReset = self._l.VCI_UsbDeviceReset
        self._VCI_UsbDeviceReset.argtypes=(c_uint32, c_uint32, c_uint32)  # (DWORD DevType,DWORD DevIndex,DWORD Reserved)
        self._VCI_UsbDeviceReset.restype = c_int32
        self._VCI_UsbDeviceReset.errcheck = self._vci_errcheck()

    def _vci_errcheck(self):
        def ret(result, func, arguments):
            log.debug(f"function {func.__name__} returned {result}")
            if result < 0:
                raise CANError(f"Device {self.device_index} (type {self.device_type}) not found", self)
            elif result == 0 and func is not self._VCI_Receive:
                raise CANError(f"Operation failed", self)
            else:
                return result
        return ret

    def OpenDevice(self):
        """
        DWORD DeviceType, DWORD DeviceInd, DWORD Reserved
        """
        return self._VCI_OpenDevice(self.device_type, self.device_index, 0)

    def CloseDevice(self):
        """
        DWORD DeviceType, DWORD DeviceInd
        """
        return self._VCI_CloseDevice(self.device_type, self.device_index)

    def InitCAN(self, CANInd, pInitConfig: VCI_INIT_CONFIG):
        """
        DWORD DeviceType, DWORD DeviceInd, DWORD CANInd, PVCI_INIT_CONFIG pInitConfig
        """
        return self._VCI_InitCAN(self.device_type, self.device_index, CANInd, byref(pInitConfig))


    def ReadBoardInfo(self, pInfo: VCI_BOARD_INFO):
        """
        DWORD DeviceType, DWORD DeviceInd, PVCI_BOARD_INFO pInfo
        """
        return self._VCI_ReadBoardInfo(self.device_type, self.device_index, byref(pInfo))


    def SetReference(self, CANInd, RefType, pData):
        """
        DWORD DeviceType, DWORD DeviceInd, DWORD CANInd, DWORD RefType, PVOID pData
        """
        return self._VCI_SetReference(self.device_type, self.device_index, CANInd, RefType, pData)


    def GetReceiveNum(self, CANInd):
        """
        DWORD DeviceType, DWORD DeviceInd, DWORD CANInd
        """
        return self._VCI_GetReceiveNum(self.device_type, self.device_index, CANInd)

    def ClearBuffer(self, CANInd):
        """
        DWORD DeviceType, DWORD DeviceInd, DWORD CANInd
        """
        return self._VCI_ClearBuffer(self.device_type, self.device_index, CANInd)


    def StartCAN(self, CANInd):
        """
        DWORD DeviceType, DWORD DeviceInd, DWORD CANInd
        """
        return self._VCI_StartCAN(self.device_type, self.device_index, CANInd)

    def ResetCAN(self, CANInd):
        """
        DWORD DeviceType, DWORD DeviceInd, DWORD CANInd
        """
        return self._VCI_ResetCAN(self.device_type, self.device_index, CANInd)


    def Transmit(self, CANInd, pSend: PVCI_CAN_OBJ, Len):
        """
        DWORD DeviceType, DWORD DeviceInd, DWORD CANInd, PVCI_CAN_OBJ pSend, ULONG Len
        """
        log.debug(f"_VCI_Transmit({self.device_type}, {self.device_index}, {CANInd}, {pSend}, {Len})")
        return self._VCI_Transmit(self.device_type, self.device_index, CANInd, pSend, Len)

    def Receive(self, CANInd, pReceive: PVCI_CAN_OBJ, Len):
        """
        DWORD DeviceType, DWORD DeviceInd, DWORD CANInd, PVCI_CAN_OBJ pReceive, ULONG Len, INT WaitTime
        """
        log.debug(f"_VCI_Receive({self.device_type}, {self.device_index}, {CANInd}, {pReceive}, {Len}, 0)")
        return self._VCI_Receive(self.device_type, self.device_index, CANInd, pReceive, Len, 0)

    def UsbDeviceReset(self):
        """
        DWORD DevType, DWORD DevIndex, DWORD Reserved
        """
        return self._VCI_UsbDeviceReset(self.device_type, self.device_index, 0)


class CANError(Exception):
    """All CAN Bus related errors."""
    def __init__(self, msg, device):
        super().__init__(msg)
        self.device = device

'''
正则替换函数声明为初始化代码的步骤：
转成python格式
\w+ (\w+) __stdcall ([\w_]+)\(([^)]+)\);
self._$2 = self._l.$2\nself._$2.argtypes=($3)\nself._$2.restype = c_int32
增加注释
(\(.*\))
$1  # $1
左边弄掉名字
(\(|, ?)(\w+) ([\w_]+)
$1$2
最后修改类型名即可。

例：
输入：
EXTERNC DWORD __stdcall VCI_OpenDevice(DWORD DeviceType,DWORD DeviceInd,DWORD Reserved);
输出：
self._VCI_OpenDevice = self._l.VCI_OpenDevice
self._VCI_OpenDevice.argtypes=(c_uint32, c_uint32, c_uint32)  # (DWORD DeviceType, DWORD DeviceInd, DWORD Reserved)
self._VCI_OpenDevice.restype = c_int32
self._VCI_OpenDevice.errcheck = self._vci_errcheck()


正则替换函数声明为Python定义：
转成Python格式：
\w+ (\w+) __stdcall ([\w_]+)\(([^)]+)\);
def $2(self, $3):\n    return self._$2($3)
逗号后面加空格
,(?! )
, （末尾空格）
去掉类型定义
(\(|, ?)(\w+) ([\w_]+)
$1$3
加注释
(.*self.*)\((.*)\)
    """\n    $2\n    """\n$1($2)
去掉VCI
def VCI_
def （末尾空格）

例：
输入：
EXTERNC DWORD __stdcall VCI_UsbDeviceReset(DWORD DevType,DWORD DevIndex,DWORD Reserved);
输出：
def VCI_UsbDeviceReset(self, DevType, DevIndex, Reserved):
    """
    DWORD DevType, DWORD DevIndex, DWORD Reserved
    """
    self._VCI_UsbDeviceReset(DevType, DevIndex, Reserved)

'''
