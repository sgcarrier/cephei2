from unittest import TestCase
from data_grabber.BLIETDataGrabber import BLIETDataGrabber
import socket
from multiprocessing import Process
import random


SENDING_ACTIVE = False
VALID_FRAME = "SRC:BLIET/ASIC1,LEN:" + \
              str((10).to_bytes(4, byteorder='little')) + \
              ",ACQ_NAME:" + str((5656).to_bytes(4, byteorder='little')) + \
              ",DATA:" + str(b'\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00') + \
              ",END!!"


class TestBLIETDataGrabber(TestCase):


    def setUp(self):
        self.filename = "test_dataGrabber.hdf5"

    def test_start(self):
        pass
        # dg = BLIETDataGrabber(bits=25)
        #
        # dg.open(self.filename)
        # dg.connectToNetwork(local_ip='127.0.0.1')
        #
        # SENDING_ACTIVE = True
        #
        # p = Process(target=self.sendUDPMulticast, args=(VALID_FRAME,))
        # p.start()
        #
        # dg.start(maxDataCount=100,
        #            filename=self.filename,
        #            datasetName="test/path",
        #            attributes=None,
        #            idFilter=5656)
        #
        # SENDING_ACTIVE = False
        # p.join()
        #
        # dg.stop()
        # dg.close()

    def test_extractData(self):
        dg = BLIETDataGrabber(bits=25)

        dataLen = 1000

        l = [random.randint(0, 0xFFFFFFFFFFFFFFFF) for i in range(dataLen)]
        byt = list_to_bytes(l)

        validFrame = bytes("SRC:BLIET/ASIC1,LEN:", 'utf-8') + \
                      (dataLen).to_bytes(4, byteorder='little') + \
                      bytes(",ACQ_NAME:", 'utf-8') + (5656).to_bytes(4, byteorder='little') + \
                      bytes(",DATA:", 'utf-8') + byt + bytes(",END!!", 'utf-8')

        for i in range(1000):
            ext_msg = dg.extractData(udp_msg=validFrame)

        self.assertEqual(ext_msg['SRC'], "BLIET/ASIC1")

    def sendUDPMulticast(self, frame):
        MCAST_GRP = '238.0.0.8'
        MCAST_PORT = 19002
        # regarding socket.IP_MULTICAST_TTL
        # ---------------------------------
        # for all packets sent, after two hops on the network the packet will not
        # be re-sent/broadcast (see https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
        MULTICAST_TTL = 2
        SENDING_ACTIVE = True

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
        while SENDING_ACTIVE:
            sock.sendto(bytes(frame, 'utf-8'), (MCAST_GRP, MCAST_PORT))



def list_to_bytes(int_list):
    out = b''
    for i in int_list:
        out += i.to_bytes(8, byteorder='little')

    return out


if __name__ == "__main__":
    t = TestBLIETDataGrabber()
    t.setUp()
    t.test_extractData()