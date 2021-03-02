import numpy as np
import pandas as pd
import logging


_logger = logging.getLogger(__name__)

class RawDataProcessor():


    RAW_TIMESTAMP_FRAME_FORMAT = {'CorrBit': {'dtype':  'B', 'offset': 52, 'bitMask':     0x01, 'bitLen':  1},
                                  'Coarse':  {'dtype': 'u4', 'offset': 48, 'bitMask':      0xF, 'bitLen':  4},
                                  'Fine':    {'dtype': 'u4', 'offset': 38, 'bitMask':    0x3FF, 'bitLen': 10},
                                  'Global':  {'dtype': 'u4', 'offset': 17, 'bitMask': 0x1FFFFF, 'bitLen': 21},
                                  'Energy':  {'dtype': 'u4', 'offset':  9, 'bitMask':     0x7F, 'bitLen':  7},
                                  'Addr':    {'dtype': 'u4', 'offset':  0, 'bitMask':    0x1FF, 'bitLen': 9}}

    PLL_TDC_FRAME_FORMAT =  {   'Fine': {'dtype': 'u4', 'offset': 10, 'bitMask': 0x3FF, 'bitLen': 10},
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
        data['DATA'] = [value for value in data['DATA'] if value > 0x5]

        data['LEN'] = len(data['DATA'])

        return data


    def reverseBits(self, data, width):
        tmp = '{:0{width}b}'.format(data, width=width)
        return int(tmp[::-1], 2)

    def raw2dict(self, data, frameFormatNum):
        format = self.getFrameFormat(frameFormatNum)
        if (format == -1):
            _logger.warning("Received incorrect dataframe format number")
            return {}

        filteredData = self.filterNonDataFrames(data)
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
