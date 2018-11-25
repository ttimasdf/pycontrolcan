import logging
import time
from ctypes import cast, byref

from controlcan import *

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

def main(*args):
    dev = ControlCAN()
    # dev.UsbDeviceReset()
    log.info("Device reset")
    dev.OpenDevice()
    log.info("Device opened")
    conf = VCI_INIT_CONFIG(baud=100)
    dev.InitCAN(0, conf)
    dev.StartCAN(0)
    log.info("CAN0 init and started")
    dev.InitCAN(1, conf)
    dev.StartCAN(1)
    log.info("CAN1 init and started")

    packet = VCI_CAN_OBJ(0x0, b'23333333')
    log.debug(f"packet {packet}")
    buf = (VCI_CAN_OBJ * 500)()
    buf_ptr = cast(buf, PVCI_CAN_OBJ)

    dev.Transmit(0, byref(packet), 1)
    log.info("Packet sent")

    recv = 0
    while not recv:
        recv = dev.Receive(1, buf_ptr, 1)
        log.info(f"{recv} packets received")

    print((buf[0].Data[:]))

    dev.CloseDevice()


if __name__ == "__main__":
    import sys

    try:
        main(*sys.argv)
    except CANError as e:
        print(f"CANbus error: {e}")
        e.device.CloseDevice()
