import socket
import h5py
import struct
import time, sys
import datetime
import logging
import numpy as np
import math
import ast
import pandas as pd
from threading import Thread
import cProfile

from processing.rawDataProcessor import RawDataProcessor

_logger = logging.getLogger(__name__)

"""
    Easy to use server to listen for multicast messages on the network
"""


class MulticastDataGrabber():


    def __init__(self):
        self.h = None
        self.data_sock = None
        self.meta_sock = None
        self._dataCount = 0
        self._startTime = None
        self._lastDataTime = None
        self.__running = False
        self.waitPeriod = datetime.timedelta(seconds=0.5)
        self.compression = None
        self.RDP = RawDataProcessor()

        self.local_acquisition_metadata = []
        self.max_acq_history = 30

        self.raw_data = 0
        self.previous_id_checked =0

        self.currentFilename = None
        self.pr = cProfile.Profile()


    def start_server(self, interface_ip='192.168.0.1', mcast_grp='238.0.0.8', data_mcast_port=19002, meta_mcast_port=19001):
        self.pr.disable()
        """Connect to the network"""
        self.connectToNetwork(mcast_grp=mcast_grp, data_mcast_port=data_mcast_port, meta_mcast_port=meta_mcast_port, interface_ip=interface_ip)

        #"""Open HDF5 file"""
        #self.open(filename=filename)

        """Start Meta data receptions"""
        thread = Thread(target= self.start_meta)
        thread.start()

        """Start Data Acquisition"""
        try:
            self.start_data()
        except KeyboardInterrupt:
            _logger.warning("Received CTRL-C, terminating server")
            #self.disp_raw_data()
            self.stop_server()
            sys.exit()

    def stop_server(self):
        self.stop()
        self.close()
        self.pr.dump_stats('out.prof')
        time.sleep(2)


    def open(self, filename, compression=None):
        self.h = h5py.File(filename, "a", libver='latest')
        self.h.swmr_mode = True
        self.compression = compression
        self.currentFilename = filename
        _logger.info("Opened file " + filename)

    def close(self):
        ##self.h.flush()
        if self.h:
            self.h.close()
            _logger.info("Closed file " + self.currentFilename)
        self.currentFilename = None


    def connectToNetwork(self, mcast_grp='238.0.0.8', data_mcast_port=19002, meta_mcast_port=19001, interface_ip='192.168.0.1'):
        """ Setup socket to listen to Cephei  multicast"""
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.data_sock.bind(('', data_mcast_port))

        # multicast specific stuff - subscribing to the IGMP multicast
        #mreq = socket.inet_aton(mcast_grp) + socket.inet_aton(socket.AF_INET)
        #group = socket.inet_aton(mcast_grp)
        #mreq = struct.pack('4sL', group, interface_ip)
        mreq = socket.inet_aton(mcast_grp) + socket.inet_aton(interface_ip)
        self.data_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # """ Setup socket to listen on multicast for meta-data"""
        # self.meta_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # self.meta_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.meta_sock.bind(('', meta_mcast_port))
        #
        # # multicast specific stuff - subscribing to the IGMP multicast
        # #mreq = socket.inet_aton(mcast_grp) + socket.inet_aton(socket.AF_INET)
        # #group = socket.inet_aton(mcast_grp)
        # #mreq = struct.pack('4sL', group, interface_ip)
        # mreq = socket.inet_aton(mcast_grp) + socket.inet_aton(interface_ip)
        # self.meta_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        _logger.info("Connected to the network")


    def start_meta(self):

        _logger.info("Starting CEPHEI Meta data reception")
        if not self.meta_sock:
            _logger.warn("Started listening without connecting to network. Using default connection setup.")
            self.connectToNetwork()

        sec = 1
        usec = 0000
        timeval = struct.pack('ll', sec, usec)
        self.meta_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)

        self.__running = True
        while self.__running:
            try:
                msg = self.meta_sock.recv(1024)
                _logger.info("here")
            except BlockingIOError:
                continue

            _logger.info("Got META data, LEN: " + str(len(msg)) + ", Payload: " + msg.decode('utf-8', 'backslashreplace'))
            rawMeta = self.extractMeta(msg)
            print(rawMeta)
            if rawMeta is None:
                continue
            else:
                alreadyIn = self.findMetaData(rawMeta['ACQ_ID'])
                if (alreadyIn != None):
                    _logger.warning("Acquisition with ACQ_ID " + str(rawMeta["ACQ_ID"]) + " already in history. Ignoring...")
                    continue
                else :
                    self.local_acquisition_metadata.insert(0, rawMeta)
                    _logger.info("Added " + str(rawMeta) + " to the acquisition history")

                    if self.currentFilename == None:
                        self.open(rawMeta['FILENAME'])
                    elif (self.currentFilename != rawMeta['FILENAME']):
                        self.close()
                        self.open(rawMeta['FILENAME'])

                    if (len(self.local_acquisition_metadata) > self.max_acq_history):
                        rem = self.local_acquisition_metadata.pop()
                        _logger.info("Removed " + str(rem) + " from the acquisition history")


    def findMetaData(self, id):
        for i in self.local_acquisition_metadata:
            print(str(i['ACQ_ID']) + " and " + str(id))

            if (i['ACQ_ID'] == id):
                return i

        return None


    def manual_data_fetch(self, formatNum=0):
        if not self.data_sock:
            return np.array([]), None


        sec = 1
        usec = 0000
        timeval = struct.pack('ll', sec, usec)
        self.data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
        self.data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4097152)

        try:
            msg = self.data_sock.recv(100 * 1024)
        except BlockingIOError:
            return np.array([]), None

        rawData = self.extractData(msg)

        if (rawData["SRC"][-1] == "1"):
            headNum = 1
        else:
            headNum = 0

        dataArr = self.RDP.raw2compArray(rawData, formatNum, keepRaw=False)

        return dataArr, headNum


    def start_data(self):
        self._startTime = datetime.datetime.now()
        self._dataCount = 0
        _logger.info("Starting CEPHEI Data grabber reception")
        if not self.data_sock:
            _logger.warn("Started listening without connecting to network. Using default connection setup.")
            self.connectToNetwork()

        sec = 1
        usec = 0000
        timeval = struct.pack('ll', sec, usec)
        self.data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
        self.data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4097152)
        counter = 0
        self.__running = True
        while self.__running:
            try:
                msg = self.data_sock.recv(100*1024)
            except BlockingIOError:
                continue

            counter = counter + 1
            self.pr.enable()


            _logger.debug("Got data NUM: " + str(counter)) # + ", LEN: " + str(len(msg)) + ", Payload: " + msg.decode('utf-8', 'backslashreplace'))
            rawData = self.extractData(msg)

            if rawData:
                metaData = self.findMetaData(rawData['ACQ_ID'])
                if metaData:
                    totalPath = (str(metaData['PATH']))
                    self.recordWithPath(rawData=rawData, path=totalPath, formatNum=metaData['FORMAT'], attributes=metaData['ATTRIBUTES'])
                    #self.record(rawData=rawData, formatNum=metaData["FORMAT"])
                else:
                    _logger.warning("Received data with no assigned metadata, ignoring.")
                    pass




    def stop(self):
        self.__running = False

    def reverseBits(self, n):
        b = '{:0{width}b}'.format(n, width=32)
        #return np.uint32(int(b[::-1], 2))
        return np.fromstring(b, dtype='S1').astype(np.uint64)

    def extractMeta(self, udp_msg):
        """ Extract the meta data from de UDP packet."""

        msg = {}
        fields = [b'ACQ_ID', b'FILENAME', b'PATH', b'FORMAT', b'ATTRIBUTES', b'END']
        for fieldPos in range(len(fields)-1):
            posStart = udp_msg.find(fields[fieldPos]) + len(fields[fieldPos]) + 1
            if posStart == -1:
                continue
            termEnd = b',' + fields[fieldPos+1]
            posEnd = udp_msg[posStart:].find(termEnd)
            if posEnd >= 0:
                posEnd = posStart + posEnd

            msg[fields[fieldPos].decode('utf-8')] = udp_msg[posStart:posEnd]

        # Meta data extraction
        if msg['ACQ_ID']:
            #msg['ACQ_ID'] =  np.frombuffer(msg['ACQ_ID'], dtype=np.uint32, count=1)
            msg['ACQ_ID'] = int.from_bytes(msg['ACQ_ID'], 'little')
            print("ACQ_ID is ")
            print(msg['ACQ_ID'])
            #msg['ACQ_ID'] = int(msg['ACQ_ID'])
        else:
            return None

        if msg['FORMAT']:
            msg['FORMAT'] = int.from_bytes(msg['FORMAT'], 'little')
            #msg['FORMAT'] = int(msg['FORMAT'])
        else:
            return None

        if msg['FILENAME']:
            msg['FILENAME'] = (msg['FILENAME']).decode('utf-8')
        else:
            return None


        if msg['ATTRIBUTES'] and msg['ATTRIBUTES'] != b'None':
            msg['ATTRIBUTES'] = ast.literal_eval(msg['ATTRIBUTES'].decode('utf-8'))
        else:
            msg['ATTRIBUTES'] = None

        if msg['PATH']:
            msg['PATH'] = (msg['PATH']).decode('utf-8')
        else:
            return None

        return msg

    def extractData(self, udp_msg):
        """ Extract the data from de UD packet."""

        msg = {}
        fields = [b'SRC', b'LEN', b'ACQ_ID', b'DATA', b'END']
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
            dt = np.dtype(np.uint64)
            dt = dt.newbyteorder('<')
            msg['DATA'] = np.frombuffer(msg['DATA'], dtype=dt, count=count) #Expecting 64 bit integers in DATA
            #vfunc = np.vectorize(self.reverseBits)
            #try:
            #    test = vfunc(tmp)
            #    msg['DATA'] = vfunc(tmp)
            #except BaseException as e:
            #    _logger.error(e)
            #    raise e

        else:
            return None

        if msg['SRC']:
            msg['SRC'] = msg['SRC'].decode('utf-8')
        else:
            return None

        if msg['ACQ_ID']:
            #msg['ACQ_ID'] =  np.frombuffer(msg['ACQ_ID'], dtype=np.uint32, count=1)
            #print(msg['ACQ_ID']
            #print(msg['ACQ_ID'])
            #msg['ACQ_ID'] = int.from_bytes(msg['ACQ_ID'], 'little')
            msg['ACQ_ID'] = int(msg['ACQ_ID'])
            print(msg['ACQ_ID'])

        else:
            return None

        return msg


    def record(self, rawData, formatNum=0, attributes=None):
        dataDict = self.RDP.raw2dict(rawData, formatNum)
        newFrame = pd.DataFrame.from_dict(rawData)

        if isinstance(self.raw_data, pd.DataFrame):
            self.raw_data = pd.concat([self.raw_data, newFrame])
        else:
            self.raw_data = newFrame


    def disp_raw_data(self):
        hist = self.raw_data.hist()

    def recordWithPath(self, rawData, path,formatNum=0, attributes=None):

        dataArr = self.RDP.raw2compArray(rawData, formatNum, keepRaw=True)

        if dataArr:
            if (path) not in self.h.keys():
                self.h.create_dataset(path, (0,), maxshape=(None,), dtype=dataArr.dtype, compression=self.compression)

            L = dataArr.shape[0]
            self.h[path].resize((self.h[path].shape[0] + L), axis=0)
            self.h[path][-L:] = dataArr

            if attributes:
                for key, val in attributes.items():
                    self.h[path].attrs[key] = val

            self.h.flush()



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    server = MulticastDataGrabber()

    server.start_server(interface_ip='192.168.0.1')