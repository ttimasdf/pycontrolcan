from ctypes import *
"""
--------------------- 
作者：yy123xiang 
来源：CSDN 
原文：https://blog.csdn.net/yy123xiang/article/details/79655661 
版权声明：本文为博主原创文章，转载请附上博文链接！
"""

class _VCI_INIT_CONFIG(Structure):
    _fields_ = [('AccCode', c_ulong),
                ('AccMask', c_ulong),
                ('Reserved', c_ulong),
                ('Filter', c_ubyte),
                ('Timing0', c_ubyte),
                ('Timing1', c_ubyte),
                ('Mode', c_ubyte)]


class _VCI_CAN_OBJ(Structure):
    _fields_ = [('ID', c_uint),
                ('TimeStamp', c_uint),
                ('TimeFlag', c_byte),
                ('SendType', c_byte),
                ('RemoteFlag', c_byte),
                ('ExternFlag', c_byte),
                ('DataLen', c_byte),
                ('Data', c_byte*8),
                ('Reserved', c_byte*3)]


vic = _VCI_INIT_CONFIG()
vic.AccCode = 0x00000000
vic.AccMask = 0xffffffff
vic.Filter = 0
vic.Timing0 = 0x00
vic.Timing1 = 0x1c
vic.Mode = 0

vco = _VCI_CAN_OBJ()
vco.ID = 0x00000001
vco.SendType = 0
vco.RemoteFlag = 0
vco.ExternFlag = 0
vco.DataLen = 8
vco.Data = (1, 2, 3, 4, 5, 6, 7, 8)


canLib = windll.LoadLibrary('./ControlCAN.dll')
print('打开设备: %d' % (canLib.VCI_OpenDevice(3, 0, 0)))
print('设置波特率: %d' % (canLib.VCI_SetReference(3, 0, 0, 0, pointer(c_int(0x060003)))))
print('初始化: %d' % (canLib.VCI_InitCAN(3, 0, 0, pointer(vic))))
print('启动: %d' % (canLib.VCI_StartCAN(3, 0, 0)))
print('清空缓冲区: %d' % (canLib.VCI_ClearBuffer(3, 0, 0)))
print('发送: %d' % (canLib.VCI_Transmit(3, 0, 0, pointer(vco), 1)))
