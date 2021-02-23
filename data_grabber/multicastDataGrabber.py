import socket
import h5py
import struct
import time
import datetime
import logging
import numpy as np
import math

from utility.rawDataProcessor import RawDataProcessor

_logger = logging.getLogger(__name__)

"""
    Easy to use server to listen for multicast messages on the network
"""


class MulticastDataGrabber():


    def __init__(self):
        self.h = None
        self.sock = None
        self._dataCount = 0
        self._startTime = None
        self._lastDataTime = None
        self.__running = False
        self.waitPeriod = datetime.timedelta(seconds=0.5)
        self.compression = None
        self.RDP = RawDataProcessor()

    def open(self, filename, compression=None):
        self.h = h5py.File(filename, "a", libver='latest')
        self.h.swmr_mode = True
        self.compression = compression

    def close(self):
        ##self.h.flush()
        if self.h:
            self.h.close()


    def connectToNetwork(self, mcast_grp='238.0.0.8', mcast_port=19002, local_ip='192.168.1.1'):

        """ Setup socket to listen to Hermes  multicast"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', mcast_port))

        # multicast specific stuff - subscribing to the IGMP multicast
        mreq = socket.inet_aton(mcast_grp) + socket.inet_aton(socket.AF_INET)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


    def start(self, maxDataCount=None, maxTime=None, filename=None, datasetName=None, attributes=None, idFilter=None):
        self._startTime = datetime.datetime.now()
        self._dataCount = 0
        _logger.info("Starting CEPHEI Data grabber reception")
        if not self.sock:
            _logger.warn("Started listening without connecting to network. Using default connection setup.")
            self.connectToNetwork()

        sec = 1
        usec = 0000
        timeval = struct.pack('ll', sec, usec)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
        scrapCaught = 0

        self.__running = True
        while self.__running:
            try:
                msg = self.sock.recv(100*1024)
            except BlockingIOError:
                continue

            _logger.debug("Got data, LEN: " + str(len(msg)) + "Payload: " + msg.decode('utf-8', 'backslashreplace'))
            rawData = self.extractData(msg)
            if rawData is None:
                continue
            if self.RESET_SENT and (rawData['ACQ_NAME'] == idFilter):
                self.RESET_SENT = False
                self._lastDataTime = datetime.datetime.now()
                #scrapCaught += 1
                continue
            if rawData and (rawData['ACQ_NAME'] == idFilter):
                _logger.debug("RAW DATA: " + str(rawData))

                if datasetName:
                    self.recordWithPath(data=rawData, path=datasetName, attributes=attributes)
                    #self.recordWithPath(data=rawData, path=datasetName, filename=filename, attributes=attributes)
                else:
                    self.record(data=rawData, filename=filename)

                self._lastDataTime = datetime.datetime.now()
            else:
                _logger.debug("Received invalid data")
                pass




    def stop(self):
        self.__running = False

    def reverseBits(self, n):
        b = '{:0{width}b}'.format(n, width=32)
        #return np.uint32(int(b[::-1], 2))
        return np.fromstring(b, dtype='S1').astype(np.uint32)

    def extractData(self, udp_msg):
        """ Extract the data from de UD packet."""

        # Type : HB
        HBMsgPos = udp_msg.find(b"HB-BLIET")
        if HBMsgPos != -1:
            return None
        # Type : Data
        msg = {}
        fields = [b'SRC', b'LEN', b'ACQ_NAME', b'DATA', b'END']
        for fieldPos in range(len(fields)-1):
            posStart = udp_msg.find(fields[fieldPos]) + len(fields[fieldPos]) + 1
            if posStart == -1:
                continue
            termEnd = b',' + fields[fieldPos+1]
            posEnd = udp_msg[posStart:].find(termEnd)
            if posEnd >= 0:
                posEnd = posStart + posEnd

            msg[fields[fieldPos].decode('utf-8')] = udp_msg[posStart:posEnd]

        # Data conversion
        if msg['DATA']:
            tmp1 = msg['DATA']
            tmp = len(msg['DATA'])
            first = msg['DATA'][0]
            count = math.floor(len(msg['DATA'])/8)
            tmp = np.frombuffer(msg['DATA'], dtype=np.uint64, count=count) #Expecting 64 bit integers in DATA
            vfunc = np.vectorize(self.reverseBits)
            try:
                msg['DATA'] = vfunc(tmp)
            except BaseException as e:
                _logger.error(e)
                raise e

        else:
            return None

        if msg['SRC']:
            msg['SRC'] = msg['SRC'].decode('utf-8')
        else:
            return None

        if msg['ACQ_NAME']:
            #msg['ACQ_NAME'] =  np.frombuffer(msg['ACQ_NAME'], dtype=np.uint32, count=1)
            msg['ACQ_NAME'] = int.from_bytes(msg['ACQ_NAME'], 'little')
        else:
            return None

        return msg


    def recordWithPath(self, data, path, formatnum=0, attributes=None):

        path = path.replace('$SRC', str(data['SRC']))

        dataDict = self.RDP.raw2dict(data, formatnum)

        for fieldName, data in dataDict.items():
            if (path + "/" + fieldName) not in self.h.keys():
                self.h.create_dataset(path + '/' + fieldName, (0,), maxshape=(None,), dtype=data.dtype, compression=self.compression)

            L = data.shape[0]
            self.h[path + "/" + fieldName].resize((self.h[path + "/" + fieldName].shape[0] + L), axis=0)
            self.h[path + "/" + fieldName][-L:] = data

            if attributes:
                for key, val in attributes.items():
                    self.h[path].attrs[key] = val

            self.h.flush()