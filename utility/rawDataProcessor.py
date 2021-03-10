import numpy as np
import pandas as pd
import logging


_logger = logging.getLogger(__name__)

RAW_TIMESTAMP_FRAME_DTYPE = np.dtype({'names': ['Addr', 'Energy', 'Global', 'Fine', 'Coarse', 'CorrBit', 'RESERVED'],
                                      'formats': ['u4', 'u4', 'u4', 'u4', 'u4', 'B', 'u4']})

PROCESSED_TIMESTAMP_FRAME_DTYPE = np.dtype({'names': ['Addr', 'Energy', 'Timestamp', 'RESERVED'],
                                      'formats': ['u4', 'u4', 'u8', 'u4']})

QKD_FRAME_DTYPE = np.dtype({'names': ['DCA', 'Bin', 'Addr', 'Timestamp', 'Window', 'PP_Type', 'Message_Type', 'Parity'],
                                      'formats': ['B', 'u4', 'u4', 'u4', 'u4', 'u4', 'u4', 'B']})

PLL_TDC_FRAME_DTYPE = np.dtype({'names': ['Coarse', 'Fine'],
                                'formats': ['u4', 'u4']})

class RawDataProcessor():

    RAW_TIMESTAMP_FRAME_FORMAT = {'RESERVED': {'dtype': 'u4', 'offset': 53, 'bitMask':    0x7FF, 'bitLen':  11},
                                  'CorrBit':  {'dtype':  'B', 'offset': 52, 'bitMask':     0x01, 'bitLen':  1},
                                  'Coarse':   {'dtype': 'u4', 'offset': 48, 'bitMask':      0xF, 'bitLen':  4},
                                  'Fine':     {'dtype': 'u4', 'offset': 38, 'bitMask':    0x3FF, 'bitLen': 10},
                                  'Global':   {'dtype': 'u4', 'offset': 17, 'bitMask': 0x1FFFFF, 'bitLen': 21},
                                  'Energy':   {'dtype': 'u4', 'offset':  9, 'bitMask':     0xFF, 'bitLen':  8},
                                  'Addr':     {'dtype': 'u4', 'offset':  0, 'bitMask':    0x1FF, 'bitLen':  9}}

    PROCESSED_TIMESTAMP_FRAME_FORMAT = {
                                  'RESERVED':    {'dtype': 'u4', 'offset': 55, 'bitMask':    0x1FF, 'bitLen': 9},
                                  'Timestamp':  {'dtype': 'u8', 'offset': 17, 'bitMask': 0xFFFFFFFFFF, 'bitLen': 38},
                                  'Energy':  {'dtype': 'u4', 'offset':  9, 'bitMask':     0xFF, 'bitLen':  8},
                                  'Addr':    {'dtype': 'u4', 'offset':  0, 'bitMask':    0x1FF, 'bitLen':  9}}

    QKD_FRAME_FORMAT = {'Parity'      : {'dtype':  'B', 'offset': 63, 'bitMask':      0x1, 'bitLen': 1},
                        'Message_Type': {'dtype': 'u4', 'offset': 60, 'bitMask':      0x7, 'bitLen': 3},
                        'PP_Type'     : {'dtype': 'u4', 'offset': 56, 'bitMask':      0xF, 'bitLen': 4},
                        'Window'      : {'dtype': 'u4', 'offset': 35, 'bitMask': 0x1FFFFF, 'bitLen': 21},
                        'Timestamp'   : {'dtype': 'u4', 'offset': 13, 'bitMask': 0x3FFFFF, 'bitLen': 22},
                        'Addr'        : {'dtype': 'u4', 'offset':  4, 'bitMask':    0x1FF, 'bitLen': 9},
                        'Bin'         : {'dtype': 'u4', 'offset':  1, 'bitMask':      0x7, 'bitLen': 3},
                        'DCA'         : {'dtype':  'B', 'offset':  0, 'bitMask':      0x1, 'bitLen': 1}}

    PLL_TDC_FRAME_FORMAT = {   'Fine': {'dtype': 'u4', 'offset': 10, 'bitMask': 0x3FF, 'bitLen': 10},
                             'Coarse': {'dtype': 'u4', 'offset':  0, 'bitMask': 0x3FF, 'bitLen': 10}}


    def __init__(self):
        self.format_reverse_bits = False
        pass

    def getFrameFormat(self, num):
        if num == 0:
            self.format_reverse_bits = False
            return self.RAW_TIMESTAMP_FRAME_FORMAT
        elif num == 1:
            self.format_reverse_bits = True
            return self.PLL_TDC_FRAME_FORMAT
        elif num == 2:
            self.format_reverse_bits = False
            return self.PROCESSED_TIMESTAMP_FRAME_FORMAT
        elif num == 3:
            self.format_reverse_bits = False
            return self.QKD_FRAME_FORMAT
        else:
            return -1

    def getFrameDtype(self, num):
        if num == 0:
            return RAW_TIMESTAMP_FRAME_DTYPE
        elif num == 1:
            return PLL_TDC_FRAME_DTYPE
        elif num == 2:
            return PROCESSED_TIMESTAMP_FRAME_DTYPE
        elif num == 3:
            return QKD_FRAME_DTYPE
        else:
            return -1

    def filterNonDataFrames(self, data):
        # The start frams
        data['DATA'] = [value for value in data['DATA'] if value != 0xAAAAAAAAAAAAAAAA]
        # The stop frame
        data['DATA'] = [value for value in data['DATA'] if value != 0xAAAAAAABAAAAAAAB]
        #garbage frames
        data['DATA'] = [value for value in data['DATA'] if value != 0xFFFFFFFFFFFFFFFF]
        # Frame type
        data['DATA'] = [value for value in data['DATA'] if value > 0xF]

        data['LEN'] = len(data['DATA'])

        return data


    def reverseBits(self, data, width):
        tmp = '{:0{width}b}'.format(data, width=width)
        return int(tmp[::-1], 2)


    def raw2compArray(self, data, frameFormatNum):
        format = self.getFrameFormat(frameFormatNum)
        if (format == -1):
            _logger.warning("Received incorrect dataframe format number")
            return None

        filteredData = self.filterNonDataFrames(data)

        dataLen = len(filteredData['DATA'])
        dtype= self.getFrameDtype(frameFormatNum)
        outArr = np.zeros(dataLen, dtype=dtype)

        for field, parameters in format.items():
            outArr[field] = (np.bitwise_and(np.right_shift(filteredData['DATA'], parameters['offset']), parameters['bitMask']))  #.as_type(parameters['dtype'])
            if self.format_reverse_bits:
                for i in range(len(outArr[field])):
                    outArr[field][i] = self.reverseBits(outArr[field][i], width=parameters['bitLen'])

        return outArr

    def raw2dict(self, data, frameFormatNum):
        format = self.getFrameFormat(frameFormatNum)
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

        format = self.getFrameFormat(frameFormatNum)
        if format == -1:
            return -1

        df = pd.DataFrame
