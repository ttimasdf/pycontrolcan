import logging
import struct
import time
import threading
from ctypes import cast, byref
from controlcan import *

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

packet_count = 2000

def t_send(device, bus_index, event_stop):
    pkts = (VCI_CAN_OBJ * packet_count)(*(VCI_CAN_OBJ(0x233, struct.pack('<I', i)) for i in range(packet_count)))
    for i in range(100):
        start = time.perf_counter()
        sen = device.Transmit(bus_index, cast(pkts, PVCI_CAN_OBJ), packet_count)
        log.info(f"sending {sen} packets {i} in {time.perf_counter()-start:.8f}s")
        if event_stop.is_set():
            return
        time.sleep(2)

def t_recv(device, bus_index, event_stop):
    buf = (VCI_CAN_OBJ * (packet_count*10))()
    for i in range(100):
        start = time.perf_counter()
        recv = device.Receive(bus_index, cast(buf, PVCI_CAN_OBJ), packet_count*10, mute=True)
        log.info(f"Receiving {recv} packets {i} in {time.perf_counter()-start:.8f}s")
        # for obj in buf:
        #     log.info(f"{obj.ID}: {obj.Data[:]}")
        time.sleep(2)
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
            log.info("Stopping background threads")
    # send.join()
    # recv.join()

    dev.CloseDevice()
    log.info("device closed")


if __name__ == "__main__":
    import sys

    try:
        main(*sys.argv)
    except CANError as e:
        e.device.CloseDevice()
        raise
