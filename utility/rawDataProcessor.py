import numpy as np
import pandas as pd
import logging


_logger = logging.getLogger(__name__)

class RawDataProcessor():


    RAW_TIMESTAMP_FRAME_FORMAT = {'CorrBit': {'dtype':  'B', 'offset': 52, 'bitMask':     0x01},
                                  'Coarse':  {'dtype': 'u4', 'offset': 48, 'bitMask':      0xF},
                                  'Fine':    {'dtype': 'u4', 'offset': 38, 'bitMask':    0x3FF},
                                  'Global':  {'dtype': 'u4', 'offset': 17, 'bitMask': 0x1FFFFF},
                                  'Energy':  {'dtype': 'u4', 'offset':  9, 'bitMask':     0x7F},
                                  'Addr':    {'dtype': 'u4', 'offset':  0, 'bitMask':    0x1FF}}

    PLL_TDC_FRAME_FORMAT =  {'CorrBit': {'dtype':  'B', 'offset': 27, 'bitMask':  0x01},
                              'Coarse': {'dtype': 'u4', 'offset': 17, 'bitMask': 0x3FF},
                                'Fine': {'dtype': 'u4', 'offset':  7, 'bitMask': 0x3FF}}


    def __init__(self):
        pass

    def getFrameFormat(self, num):
        if num == 0:
            return self.RAW_TIMESTAMP_FRAME_FORMAT
        elif num == 1:
            return self.PLL_TDC_FRAME_FORMAT
        else:
            return -1

    def filterNonDataFrames(self, data):
        # The start frams
        data['DATA'] = [value for value in data['DATA'] if value != 0xAAAAAAAAAAAAAAAA]
        # The stop frame
        data['DATA'] = [value for value in data['DATA'] if value != 0xAAAAAAABAAAAAAAB]
        # Frame type
        data['DATA'] = [value for value in data['DATA'] if value > 0x5]

        data['LEN'] = len(data['DATA'])

        return data


    def raw2dict(self, data, frameFormatNum):
        format = self.getFrameFormat(frameFormatNum)
        if (format == -1):
            _logger.warning("Received incorrect dataframe format number")
            return {}

        filteredData = self.filterNonDataFrames(data)

        outDict = {}
        for field, parameters in format.items():
            outDict[field] = (np.bitwise_and(np.right_shift(filteredData['DATA'], parameters['offset']), parameters['bitMask']))  #.as_type(parameters['dtype'])

        return outDict


    def raw2df(self, data, frameFormatNum):

        format = self.getFrameFormat(frameFormatNum)
        if format == -1:
            return -1

        df = pd.DataFrame
