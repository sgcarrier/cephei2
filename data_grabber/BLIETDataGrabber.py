import socket
import h5py
import struct
import time
import datetime
import logging
import numpy as np
import math
from control import BLIETControl
from control.BLIETControl import Platform

_logger = logging.getLogger(__name__)

"""
    Easy to use server to listen for multicast messages on the network
"""


class BLIETDataGrabber:

    def __init__(self, bits=21):
        self.h = None
        self.sock = None
        self._dataCount = 0
        self._startTime = None
        self._lastDataTime = None
        self.__running = False
        self.waitPeriod = datetime.timedelta(seconds=0.5)
        self.compression = None
        self.p = Platform()
        self.RESET_SENT = False
        if bits == 25:
            self.frameMask = 0x1FFFFFF
            self.packetFields = {'CorrBit': {'dtype': 'B', 'offset': 31, 'bitMask': 0x01},
                             'Coarse': {'dtype': 'u4', 'offset': 23, 'bitMask': 0xFF},
                             'Mid': {'dtype': 'u4', 'offset': 15, 'bitMask': 0xFF},
                             'Fine': {'dtype': 'u4', 'offset': 7, 'bitMask': 0xFF}}
        elif bits == 21:
            self.frameMask = 0x1FFFFFF
            self.packetFields = {'CorrBit': {'dtype': 'B', 'offset': 27, 'bitMask': 0x01},
                                 'Coarse': {'dtype': 'u4', 'offset': 17, 'bitMask': 0x3FF},
                                 'Fine': {'dtype': 'u4', 'offset': 7, 'bitMask': 0x3FF}}

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
        mreq = socket.inet_aton(mcast_grp) + socket.inet_aton(local_ip)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def start(self, maxDataCount=None, maxTime=None, filename=None, datasetName=None, attributes=None, idFilter=None):
        self._startTime = datetime.datetime.now()
        self._dataCount = 0
        _logger.info("Starting HERMES Data grabber reception")
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
                meetAllConditions, idFilter = self.conditionalActions(maxDataCount, maxTime, idFilter)
                if meetAllConditions:
                    self.stop()
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

            if self.validateStopChecks(maxDataCount=maxDataCount, maxTime=maxTime):
                self.stop()



    def stop(self):
        self.__running = False

    def extractDataOld(self, udp_msg):
        """ Extract the data from de UD packet."""

        try:
            if udp_msg.decode('utf-8') == "HB-BLIET":
                return None
        except:
            pass

        msg = {}

        msg['SRC'] = 'BLIET/ASIC1'
        msg['LEN'] = udp_msg[20:24]
        msg['DATA'] = udp_msg[40:]
        ct = len(msg['DATA'])


        if msg['DATA']:
            #count = math.floor(int.from_bytes(msg['LEN'], byteorder='big', signed=False))
            count = math.floor(len(msg['DATA'])/8)
            tmp = np.frombuffer(msg['DATA'], dtype=np.uint64, count=count)
            #tmp1 = tmp.byteswap(inplace=False)
            vfunc = np.vectorize(self.reverseBits)
            msg['DATA'] = vfunc(tmp)



        #Add more processing here if need be

        return msg

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


        # for field in [b'SRC', b'LEN', b'ACQ_NAME', b'DATA', b'END']:
        #     posStart = udp_msg.find(field) + len(field) + 1
        #     if posStart == -1:
        #         continue
        #     posEnd = udp_msg[posStart:].find(b',')
        #     if posEnd >= 0:
        #         posEnd = posStart + posEnd
        #
        #     msg[field.decode('utf-8')] = udp_msg[posStart:posEnd]

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

    def recordWithPath(self, data, path, attributes=None):

        path = path.replace('$SRC', str(data['SRC']))


        for fieldName, format in self.packetFields.items():
            if (path + "/" + fieldName) not in self.h.keys():
                self.h.create_dataset(path + '/' + fieldName, (0,), maxshape=(None,), dtype=format['dtype'], compression=self.compression)
        # if atstributes:
        #     for attrName, value in attributes.items():
        #         h[path].attrs[attrName] = value
        if type(data['DATA']) is dict:
            pass
        else :
            filtered_data = data['DATA'][(data['DATA'] & self.frameMask) != 0]
            filtered_data = filtered_data[(filtered_data & self.frameMask) != self.frameMask]
            # filter out Fine = 0 and 255
            if 'Fine' in self.packetFields.keys():
                filtered_data = filtered_data[((filtered_data >> self.packetFields['Fine']['offset']) & self.packetFields['Fine']['bitMask']) != 0]
                filtered_data = filtered_data[((filtered_data >> self.packetFields['Fine']['offset']) & self.packetFields['Fine']['bitMask']) != 255]
                if len(filtered_data) == 0:
                    return

            if 'Mid' in self.packetFields.keys():
                filtered_data = filtered_data[((filtered_data >> self.packetFields['Mid']['offset']) & self.packetFields['Mid']['bitMask']) != 0]
                filtered_data = filtered_data[((filtered_data >> self.packetFields['Mid']['offset']) & self.packetFields['Mid']['bitMask']) != 255]
                if len(filtered_data) == 0:
                    return

            if 'Coarse' in self.packetFields.keys():
                filtered_data = filtered_data[((filtered_data >> self.packetFields['Coarse']['offset']) & self.packetFields['Coarse']['bitMask']) != 0]
                filtered_data = filtered_data[((filtered_data >> self.packetFields['Coarse']['offset']) & self.packetFields['Coarse']['bitMask']) != 255]
                if len(filtered_data) == 0:
                    return

            L = len(filtered_data)
            for fieldName, format in self.packetFields.items():
                self.h[path + "/" + fieldName].resize((self.h[path + "/" + fieldName].shape[0] + L), axis=0)
                self.h[path + "/" + fieldName][-L:] = (filtered_data >> format['offset']) & format['bitMask']
            self._dataCount += L

            self.h['BLIET'].attrs['CurrSetRef'] = self.h[path].ref

            if attributes:
                for key, val in attributes.items():
                    self.h[path].attrs[key] = val

            self.h.flush()


    # def recordWithPath(self, data, path, filename, attributes=None):
    #
    #     path = path.replace('$SRC', str(data['SRC']))
    #
    #     with h5py.File(filename, "a", swmr=True, libver='latest') as h:
    #
    #         for fieldName, format in self.packetFields.items():
    #             if (path + "/" + fieldName) not in h.keys():
    #                 h.create_dataset(path + '/' + fieldName, (0,), maxshape=(None,), dtype=format['dtype'])
    #         # if attributes:
    #         #     for attrName, value in attributes.items():
    #         #         h[path].attrs[attrName] = value
    #         if type(data['DATA']) is dict:
    #             pass
    #         else :
    #             L = len(data['DATA'])
    #             for fieldName, format in self.packetFields.items():
    #                 h[path + "/" + fieldName].resize((h[path + "/" + fieldName].shape[0] + L), axis=0)
    #                 h[path + "/" + fieldName][-L:] = (data['DATA'] >> format['offset']) & format['bitMask']
    #             self._dataCount += L
    #             h.flush()

    def reverseBitsOld(self, n):
        result = np.uint32(0)
        n = np.uint32(n)
        one = np.uint32(1)
        for i in range(32):
            result = np.left_shift(result, one)
            result = np.bitwise_or((np.bitwise_and(n,one)), result)
            n = np.right_shift(n, one)
        return result

    def reverseBits(self, n):
        b = '{:0{width}b}'.format(n, width=32)
        #return np.uint32(int(b[::-1], 2))
        return np.fromstring(b, dtype='S1').astype(np.uint32)


    def validateStopChecks(self, maxDataCount=None, maxTime=None):
        if maxDataCount:
            if maxDataCount <= self._dataCount:
                return True
            else:
                _logger.info("Progress: " + str(self._dataCount) + "/" + str(maxDataCount) )

        if maxTime:
            t = datetime.datetime.now()
            if maxTime <= ( t - self._startTime):
                return True

        return False

    def conditionalActions(self, maxCount, maxTime, currID):
        if self._lastDataTime == None:
            self._lastDataTime =datetime.datetime.now()

        if self.waitPeriod <= (datetime.datetime.now() - self._lastDataTime):
            _logger.warn("Haven't received data in " + str((datetime.datetime.now() - self._lastDataTime)) + " seconds, so sending a REINIT")
            self.p.ICSSHSR4.RESET(0)
            self.p.CORE.STOP_ACQUISITION(0)
            currID = BLIETControl.genValidAcqID()
            self.p.CORE.START_ACQUISITION(currID)

            self.RESET_SENT = True
            self._lastDataTime = datetime.datetime.now()

        return self.validateStopChecks(maxCount, maxTime), currID



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    BDG = BLIETDataGrabber()
    baseDatesetPath = "$SRC/DVTO0/NON_CORR/"
    config = "VREF_{0}/SLOW_{1}/FAST_{2}".format(0, 0, 0)
    attributes = {'VP_REF': 0, 'VN_REF': 1, 'VP_SLOW': 2,'VN_SLOW': 3,'VP_FAST': 4, 'VN_FAST': 5, 'SLOW': 6, 'FAST': 7}

    BDG.start(filename="TEST_NEW_FORMAT.hdf5", datasetName=baseDatesetPath+config, attributes=attributes)
    print("DONE!")
