import numpy as np
import pandas as pd
import logging
from processing.dataFormats import *
from tqdm import tqdm


_logger = logging.getLogger(__name__)


class RawDataProcessor():

    def __init__(self):
        self.format_reverse_bits = False
        pass

    def filterNonDataFrames(self, data):
        # The start frams
        data['DATA'] = [value for value in data['DATA'] if value != 0xAAAAAAAAAAAAAAAA]
        # The stop frame
        data['DATA'] = [value for value in data['DATA'] if value != 0xAAAAAAABAAAAAAAB]
        #garbage frames
        data['DATA'] = [value for value in data['DATA'] if value != 0xFFFFFFFFFFFFFFFF]
        # Frame type
        data['DATA'] = [value for value in data['DATA'] if (value >> np.uint64(24)) > 0xF]

        data['LEN'] = len(data['DATA'])

        return data


    def reverseBits(self, data, width):
        tmp = '{:0{width}b}'.format(data, width=width)
        return int(tmp[::-1], 2)


    def packagedData(self, data):
        """Currently drops frames between packets. This can be fixed using class members to
        store the state of the acquisition when we know for sure that there is no data dropped
        by other systems """
        ack = 0
        first_frame = False
        index = 0
        for value in data['DATA']:
            if value == 0xAAAAAAAAAAAAAAAA:
                ack = 1
                first_frame = True
            elif value == 0xAAAAAAABAAAAAAAB:
                ack = 0
                first_frame = False
            elif value == 0xFFFFFFFFFFFFFFFF:
                ack = 0
                first_frame = False
            elif first_frame and ack:
                # TODO: value = firstFrame
                first_frame = False
            elif ack:
                # TODO: value = data
                index += 1
            else:
                # Droped data
                pass
        # TODO
        return data


    def raw2compArray(self, data, frameFormatNum, keepRaw=False):
        format, self.format_reverse_bits = getFrameFormat(frameFormatNum, keepRaw=keepRaw)
        if (format == -1):
            _logger.warning("Received incorrect dataframe format number")
            return None

        filteredData = self.filterNonDataFrames(data)

        dataLen = len(filteredData['DATA'])
        dtype = getFrameDtype(frameFormatNum, keepRaw=keepRaw)
        outArr = np.zeros(dataLen, dtype=dtype)

        if dataLen == 0:
            return None

        for field, parameters in (format.items()):
            outArr[field] = (np.bitwise_and(np.right_shift(filteredData['DATA'], parameters['offset']), parameters['bitMask']))  #.as_type(parameters['dtype'])
            if self.format_reverse_bits:
                for i in range(len(outArr[field])):
                    outArr[field][i] = self.reverseBits(outArr[field][i], width=parameters['bitLen'])

        return outArr

    def raw2dict(self, data, frameFormatNum):
        format = getFrameFormat(frameFormatNum)
        if (format == -1):
            _logger.warning("Received incorrect dataframe format number")
            return {}

        filteredData = self.filterNonDataFrames(data)
        #filteredData = data
        _logger.info("RAW = " + str(len(filteredData['DATA'])))
        #filteredData = data

        outDict = {}
        for field, parameters in format.items():
            outDict[field] = (np.bitwise_and(np.right_shift(filteredData['DATA'], parameters['offset']), parameters['bitMask']))  #.as_type(parameters['dtype'])
            if self.format_reverse_bits:
                for i in range(len(outDict[field])):
                    outDict[field][i] = self.reverseBits(outDict[field][i], width=parameters['bitLen'])

        return outDict


    def raw2df(self, data, frameFormatNum):

        format = getFrameFormat(frameFormatNum)
        if format == -1:
            return -1

        df = pd.DataFrame
