import logging
import queue
import struct
import time
import threading
from ctypes import cast, byref, c_ubyte
from controlcan import *

log = logging.getLogger()
log.setLevel(logging.INFO)


def t_send(device, bus_index, event_stop, q):
    bulk_count = 1000
    while True:
        pkts =  (VCI_CAN_OBJ * bulk_count)()
        for i in range(bulk_count):
            try:
                pid, data = q.get(timeout=2)
            except queue.Empty as e:
                break
            else:
                pkts[i].ID = pid
                if isinstance(data, int):
                    pkts[i].Data = (c_ubyte*8)(*struct.pack('<I', data))
                elif isinstance(data, bytes):
                    pkts[i].Data = (c_ubyte*8)(*data)
                else:
                    log.warning(f"data {data} not available")
                q.task_done()
        if i > 0:
            start = time.perf_counter()
            sen = device.Transmit(bus_index, cast(pkts, PVCI_CAN_OBJ), i)
            log.info(f"sending {bulk_count} packets to id {pid:08x} in {time.perf_counter()-start:.8f}s")
        if event_stop.is_set():
            return

def t_recv(device, bus_index, event_stop, q):
    buf_size = 5000
    buf = (VCI_CAN_OBJ * buf_size)()
    while True:
        start = time.perf_counter()
        recv = device.Receive(bus_index, cast(buf, PVCI_CAN_OBJ), buf_size, mute=True)
        log.debug(f"Receiving {recv} packets in {time.perf_counter()-start:.8f}s")
        for n in range(recv):
            obj = buf[n]
            log.debug(f"{obj.ID:08x}: {obj.Data[:]}")
            q.put((obj.ID, obj.Data[:]))
        if event_stop.is_set():
            return
        time.sleep(0.5)



def main(*args):
    dev = ControlCAN()
    # dev.UsbDeviceReset()
    # log.info("Device reset")
    dev.OpenDevice(block=True)
    log.info("Device opened")
    conf = VCI_INIT_CONFIG(baud=100)
    dev.InitCAN(0, conf)
    time.sleep(0.5)
    dev.StartCAN(0)
    log.info("CAN0 init and started")
    dev.InitCAN(1, conf)
    time.sleep(0.5)
    dev.StartCAN(1)
    log.info("CAN1 init and started")

    stop = threading.Event()
    qsend = queue.Queue()
    qrecv = queue.Queue()
    send = threading.Thread(target=t_send, args=(dev, 0, stop, qsend))
    recv = threading.Thread(target=t_recv, args=(dev, 0, stop, qrecv))
    send.start()
    recv.start()

    if '-i' in args:
        try:
            from ptpython.repl import embed
        except ImportError as e:
            import pdb
        else:
            have_ptpython = True

        log.info("to stop background threads, run stop.set()")
        if have_ptpython:
            embed(globals(), locals())
        else:
            pdb.set_trace()

        stop.set()
        log.info("Stopping background threads")
        send.join()
        recv.join()
    else:
        while send.is_alive() or recv.is_alive():
            if stop.is_set():
                log.info("still waiting for finish")
            # Use time.sleep instead of join to void signal stuck because of GIL
            try:
                time.sleep(1)
            except KeyboardInterrupt as e:
                stop.set()
                log.info("Stopping background threads")


    dev.CloseDevice()
    log.info("device closed")


if __name__ == "__main__":
    import sys

    if '-d' in sys.argv:
        logging.basicConfig(filename="debug.log", level=logging.DEBUG)
    else:
        logging.basicConfig()
    try:
        main(*sys.argv)
    except CANError as e:
        e.device.CloseDevice()
        raise
