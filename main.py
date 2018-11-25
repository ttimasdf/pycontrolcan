from controlcan import *
import time

def main(*args):
    dev = ControlCAN()
    #dev.UsbDeviceReset()
    print("device reset")
    dev.OpenDevice()
    print("open success")
    conf = VCI_INIT_CONFIG(baud=100)
    dev.InitCAN(0, conf)
    print("init CAN0")
    dev.InitCAN(1, conf)
    print("init CAN1")
    packet = VCI_CAN_OBJ(0x0, b'23333333')
    print(f"packet {packet}")
    buf = (VCI_CAN_OBJ * 500)()
    buf_ptr = cast(buf, PVCI_CAN_OBJ)

    dev.Transmit(0, byref(packet), 1)
    print("Sent packet")

    recv = 0
    while not recv:
        recv = dev.Receive(1, byref(packet), 1)
        print(f"{recv} packets received")
    
    print((buf[0].Data[:]))

    dev.CloseDevice()


if __name__ == "__main__":
    import sys
    main(*sys.argv)
