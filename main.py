import logging
import struct
import time
import threading
from ctypes import cast, byref
from controlcan import *

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


def t_send(device, bus_index, event_stop):
    for i in range(100):
        pkts = (VCI_CAN_OBJ * 10)(*(VCI_CAN_OBJ(0x233, struct.pack('<I', i)) for i in range(10)))
        sen = device.Transmit(bus_index, cast(pkts, PVCI_CAN_OBJ), 10)
        log.info(f"sending {sen} packets {i}")
        if event_stop.is_set():
            return
        time.sleep(3)


def t_recv(device, bus_index, event_stop):
    for i in range(100):
        # pkts = (VCI_CAN_OBJ * 10)(*(VCI_CAN_OBJ(0x233, struct.pack('<I', i)) for i in range(10)))
        buf = (VCI_CAN_OBJ * 10)()
        recv = device.Receive(bus_index, cast(buf, PVCI_CAN_OBJ), 10, mute=True)
        log.info(f"Receiving {recv} packets {i}")
        for obj in buf:
            log.debug(f"{obj.ID}: {obj.Data[:]}")
        time.sleep(1)
        if event_stop.is_set():
            return


def main(*args):
    dev = ControlCAN()
    # dev.UsbDeviceReset()
    # log.info("Device reset")
    dev.OpenDevice(block=True)
    log.info("Device opened")
    conf = VCI_INIT_CONFIG(baud=100)
    dev.InitCAN(0, conf)
    dev.StartCAN(0)
    log.info("CAN0 init and started")
    dev.InitCAN(1, conf)
    dev.StartCAN(1)
    log.info("CAN1 init and started")

    stop = threading.Event()
    send = threading.Thread(target=t_send, args=(dev, 0, stop))
    recv = threading.Thread(target=t_recv, args=(dev, 1, stop))
    send.start()
    recv.start()

    while send.is_alive() or recv.is_alive():
        log.info("still waiting for finish")
        # Use time.sleep instead of join to void signal stuck because of GIL
        # TODO send signal to threads to stop them
        try:
            time.sleep(10)
        except KeyboardInterrupt as e:
            stop.set()
    # send.join()
    # recv.join()

    dev.CloseDevice()


if __name__ == "__main__":
    import sys

    try:
        main(*sys.argv)
    except CANError as e:
        e.device.CloseDevice()
        raise
