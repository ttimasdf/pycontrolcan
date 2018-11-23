#/usr/bin/env python3
#https://blog.csdn.net/caimouse/article/details/51749579
#开发人员：蔡军生（QQ：9073204） 深圳  2018-3-25
#
# --------------------- 
# 作者：caimouse 
# 来源：CSDN 
# 原文：https://blog.csdn.net/caimouse/article/details/79692118 
# 版权声明：本文为博主原创文章，转载请附上博文链接！

from ctypes import *
 
VCI_USBCAN2A = 4
STATUS_OK = 1
class VCI_INIT_CONFIG(Structure):  
    _fields_ = [("AccCode", c_ulong),
                ("AccMask", c_ulong),
                ("Reserved", c_ulong),
                ("Filter", c_ubyte),
                ("Timing0", c_ubyte),
                ("Timing1", c_ubyte),
                ("Mode", c_ubyte)
                ]  
class VCI_CAN_OBJ(Structure):  
    _fields_ = [("ID", c_uint),
                ("TimeStamp", c_uint),
                ("TimeFlag", c_ubyte),
                ("SendType", c_ubyte),
                ("RemoteFlag", c_ubyte),
                ("ExternFlag", c_ubyte),
                ("DataLen", c_ubyte),
                ("Data", c_ubyte*8),
                ("Reserved", c_ubyte*3)
                ] 
 
CanDLLName = 'ControlCAN.dll' #DLL是32位的，必须使用32位的PYTHON
canDLL = windll.LoadLibrary(CanDLLName)
print(CanDLLName)
 
ret = canDLL.VCI_OpenDevice(VCI_USBCAN2A, 0, 0)
print(ret)
if ret != STATUS_OK:
    print('调用 VCI_OpenDevice出错\r\n')
 
#初始0通道
vci_initconfig = VCI_INIT_CONFIG(0x80000008, 0xFFFFFFFF, 0,
                                 2, 0x00, 0x1C, 0)
ret = canDLL.VCI_InitCAN(VCI_USBCAN2A, 0, 0, byref(vci_initconfig))
if ret != STATUS_OK:
    print('调用 VCI_InitCAN出错\r\n')
 
ret = canDLL.VCI_StartCAN(VCI_USBCAN2A, 0, 0)
if ret != STATUS_OK:
    print('调用 VCI_StartCAN出错\r\n')
 
#初始1通道
ret = canDLL.VCI_InitCAN(VCI_USBCAN2A, 0, 1, byref(vci_initconfig))
if ret != STATUS_OK:
    print('调用 VCI_InitCAN 1 出错\r\n')
 
ret = canDLL.VCI_StartCAN(VCI_USBCAN2A, 0, 1)
if ret != STATUS_OK:
    print('调用 VCI_StartCAN 1 出错\r\n')
 
#通道0发送数据
ubyte_array = c_ubyte*8
a = ubyte_array(1,2,3,4, 5, 6, 7, 64)
ubyte_3array = c_ubyte*3
b = ubyte_3array(0, 0 , 0)
vci_can_obj = VCI_CAN_OBJ(0x0, 0, 0, 1, 0, 0,  8, a, b)
 
ret = canDLL.VCI_Transmit(VCI_USBCAN2A, 0, 0, byref(vci_can_obj), 1)
if ret != STATUS_OK:
    print('调用 VCI_Transmit 出错\r\n')
 
#通道1接收数据
a = ubyte_array(0, 0, 0, 0, 0, 0, 0, 0)
vci_can_obj = VCI_CAN_OBJ(0x0, 0, 0, 1, 0, 0,  8, a, b)
ret = canDLL.VCI_Receive(VCI_USBCAN2A, 0, 1, byref(vci_can_obj), 1, 0)
print(ret)
while ret <= 0:
    print('调用 VCI_Receive 出错\r\n')
    ret = canDLL.VCI_Receive(VCI_USBCAN2A, 0, 1, byref(vci_can_obj), 1, 0)
if ret > 0:
    print(vci_can_obj.DataLen)
    print(list(vci_can_obj.Data))
 
#关闭
canDLL.VCI_CloseDevice(VCI_USBCAN2A, 0)
