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
    bulk_count = 100
    while True:
        for pid in range(0xfff):
            pkts = send_int(pid, 0xffffffff, bulk_count)
            for rep in range(2):
                start = time.perf_counter()
                sen = device.Transmit(bus_index, cast(pkts, PVCI_CAN_OBJ), bulk_count)
                log.info(f"sending {bulk_count}*{rep} packets to id {pid:08x} in {time.perf_counter()-start:.8f}s")
                if event_stop.is_set():
                    return
                time.sleep(0.01)

def t_recv(device, bus_index, event_stop):
    buf = (VCI_CAN_OBJ * (packet_count*10))()
    for i in range(100):
        start = time.perf_counter()
        recv = device.Receive(bus_index, cast(buf, PVCI_CAN_OBJ), packet_count*10, mute=True)
        log.info(f"Receiving {recv} packets {i} in {time.perf_counter()-start:.8f}s")
        for n in range(recv):
            obj = buf[n]
            log.debug(f"{obj.ID:08x}: {obj.Data[:]}")
        time.sleep(0.3)
        if event_stop.is_set():
            return

def send_int(id, num, times):
    return (VCI_CAN_OBJ * times)(*(VCI_CAN_OBJ(id, struct.pack('<I', num)) for i in range(times)))

def recv_handler(id, data):
    pass


def main(*args):
    dev = ControlCAN()
    # dev.UsbDeviceReset()
    # log.info("Device reset")
    dev.OpenDevice(block=True)
    log.info("Device opened")
    conf = VCI_INIT_CONFIG(baud=100)
    dev.InitCAN(0, conf)
    time.sleep(0.1)
    dev.StartCAN(0)
    log.info("CAN0 init and started")
    dev.InitCAN(1, conf)
    time.sleep(0.1)
    dev.StartCAN(1)
    log.info("CAN1 init and started")

    stop = threading.Event()
    send = threading.Thread(target=t_send, args=(dev, 0, stop))
    recv = threading.Thread(target=t_recv, args=(dev, 0, stop))
    send.start()
    # recv.start()

    while send.is_alive() or recv.is_alive():
        if stop.is_set():
            log.info("still waiting for finish")
        # Use time.sleep instead of join to void signal stuck because of GIL
        try:
            time.sleep(1)
        except KeyboardInterrupt as e:
            stop.set()
            log.info("Stopping background threads")
    # send.join()
    # recv.join()

    dev.CloseDevice()
    log.info("device closed")


if __name__ == "__main__":
    import sys

    if '-d' in sys.argv:
        log.setLevel(logging.DEBUG)
    try:
        main(*sys.argv)
    except CANError as e:
        e.device.CloseDevice()
        raise
