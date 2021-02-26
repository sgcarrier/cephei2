import socket
import h5py
import struct
import time, sys
import datetime
import logging
import numpy as np
import math
from threading import Thread

from utility.rawDataProcessor import RawDataProcessor

from data_grabber.multicastDataGrabber import MulticastDataGrabber

_logger = logging.getLogger(__name__)




class MulticastAcquisitionManager():


    def __init__(self):
        self.meta_sock = None

        self.__running = False
        self.waitPeriod = datetime.timedelta(seconds=0.5)
        self.compression = None

        self.local_acquisition_metadata = []
        self.local_acquisition_servers = []
        self.max_acq_history = 30


    def connectToNetwork(self, mcast_grp='238.0.0.8', meta_mcast_port=19001):

        """ Setup socket to listen on multicast for meta-data"""
        self.meta_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.meta_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.meta_sock.bind(('', meta_mcast_port))

        # multicast specific stuff - subscribing to the IGMP multicast
        #mreq = socket.inet_aton(mcast_grp) + socket.inet_aton(socket.AF_INET)
        group = socket.inet_aton(mcast_grp)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.meta_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        _logger.info("Connected to the network")

    def stop(self):
        self.__running = False


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
                    if (len(self.local_acquisition_metadata) > self.max_acq_history):
                        rem = self.local_acquisition_metadata.pop()
                        _logger.info("Removed " + str(rem) + " from the acquisition history")


    def findMetaData(self, id):
        for i in self.local_acquisition_metadata:
            if (i['ACQ_ID'] == id):
                return i

        return None

    def extractMeta(self, udp_msg):
        """ Extract the meta data from de UDP packet."""

        msg = {}
        fields = [b'ACQ_ID', b'PATH', b'FORMAT', b'END']
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
        else:
            return None

        if msg['FORMAT']:
            msg['FORMAT'] = int.from_bytes(msg['FORMAT'], 'little')
        else:
            return None

        if msg['PATH']:
            msg['PATH'] = (msg['PATH']).decode('utf-8')
        else:
            return None

        return msg