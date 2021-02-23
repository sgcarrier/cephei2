import numpy as np
import pandas as pd





class RawDataProcessor():


    RAW_TIMESTAMP_FRAME_FORMAT = {'CorrBit': {'dtype':  'B', 'offset': 52, 'bitMask':     0x01},
                                  'Coarse':  {'dtype': 'u4', 'offset': 48, 'bitMask':      0xF},
                                  'Fine':    {'dtype': 'u4', 'offset': 38, 'bitMask':    0x3FF},
                                  'Global':  {'dtype': 'u4', 'offset': 17, 'bitMask': 0x1FFFFF},
                                  'Energy':  {'dtype': 'u4', 'offset':  9, 'bitMask':     0x7F},
                                  'Addr':    {'dtype': 'u4', 'offset':  0, 'bitMask':    0x1FF}}


    def __init__(self):
        pass

    def getFrameFormat(self, num):
        if num == 0:
            return self.RAW_TIMESTAMP_FRAME_FORMAT
        else:
            return -1

    def raw2dict(self, data, frameFormatNum):
        format = self.getFrameFormat(frameFormatNum)
        outDict = {}
        for field, parameters in format.items():
            outDict[field] = (np.bitwise_and(np.right_shift(data, parameters['offset']), parameters['bitMask'])).as_type(parameters['dtype'])

        return outDict


    def raw2df(self, data, frameFormatNum):

        format = self.getFrameFormat(frameFormatNum)
        if format == -1:
            return -1

        df = pd.DataFrame
