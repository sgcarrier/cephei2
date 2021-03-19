import numpy as np


RAW_TIMESTAMP_FRAME_DTYPE = np.dtype({'names': ['Addr', 'Energy', 'Global', 'Fine', 'Coarse', 'CorrBit', 'RESERVED'],
                                      'formats': ['u2', 'u1', 'u4', 'u2', 'u1', 'B', 'u2']})

PROCESSED_TIMESTAMP_FRAME_DTYPE = np.dtype({'names': ['Addr', 'Energy', 'Timestamp', 'RESERVED'],
                                      'formats': ['u2', 'u1', 'u8', 'u2']})

QKD_FRAME_DTYPE = np.dtype({'names': ['DCA', 'Bin', 'Addr', 'Timestamp', 'Window', 'PP_Type', 'Message_Type', 'Parity'],
                                      'formats': ['B', 'u4', 'u4', 'u4', 'u4', 'u4', 'u4', 'B']})

PLL_TDC_FRAME_DTYPE = np.dtype({'names': ['Coarse', 'Fine'],
                                'formats': ['u4', 'u4']})

RAW_TIMESTAMP_FRAME_DTYPE_WRAW = np.dtype({'names': ['Addr', 'Energy', 'Global', 'Fine', 'Coarse', 'CorrBit', 'RESERVED', 'RAW'],
                                      'formats': ['u4', 'u4', 'u4', 'u4', 'u4', 'B', 'u4', 'u8']})

PROCESSED_TIMESTAMP_FRAME_DTYPE_WRAW = np.dtype({'names': ['Addr', 'Energy', 'Timestamp', 'RESERVED', 'RAW'],
                                      'formats': ['u4', 'u4', 'u8', 'u4', 'u8']})

QKD_FRAME_DTYPE_WRAW = np.dtype({'names': ['DCA', 'Bin', 'Addr', 'Timestamp', 'Window', 'PP_Type', 'Message_Type', 'Parity', 'RAW'],
                                      'formats': ['B', 'u4', 'u4', 'u4', 'u4', 'u4', 'u4', 'B', 'u8']})

PLL_TDC_FRAME_DTYPE_WRAW = np.dtype({'names': ['Coarse', 'Fine', 'RAW'],
                                'formats': ['u4', 'u4', 'u8']})


########################

RAW_TIMESTAMP_FRAME_FORMAT = {'RESERVED': {'dtype': 'u2', 'offset': 53, 'bitMask': 0x7FF, 'bitLen': 11},
                              'CorrBit': {'dtype': 'B', 'offset': 52, 'bitMask': 0x01, 'bitLen': 1},
                              'Coarse': {'dtype': 'u1', 'offset': 48, 'bitMask': 0xF, 'bitLen': 4},
                              'Fine': {'dtype': 'u2', 'offset': 38, 'bitMask': 0x3FF, 'bitLen': 10},
                              'Global': {'dtype': 'u4', 'offset': 17, 'bitMask': 0x1FFFFF, 'bitLen': 21},
                              'Energy': {'dtype': 'u1', 'offset': 9, 'bitMask': 0xFF, 'bitLen': 8},
                              'Addr': {'dtype': 'u2', 'offset': 0, 'bitMask': 0x1FF, 'bitLen': 9}}

PROCESSED_TIMESTAMP_FRAME_FORMAT = {
    'RESERVED': {'dtype': 'u2', 'offset': 55, 'bitMask': 0x1FF, 'bitLen': 9},
    'Timestamp': {'dtype': 'u8', 'offset': 17, 'bitMask': 0xFFFFFFFFFF, 'bitLen': 38},
    'Energy': {'dtype': 'u1', 'offset': 9, 'bitMask': 0xFF, 'bitLen': 8},
    'Addr': {'dtype': 'u2', 'offset': 0, 'bitMask': 0x1FF, 'bitLen': 9}}

QKD_FRAME_FORMAT = {'Parity': {'dtype': 'B', 'offset': 63, 'bitMask': 0x1, 'bitLen': 1},
                    'Message_Type': {'dtype': 'u4', 'offset': 60, 'bitMask': 0x7, 'bitLen': 3},
                    'PP_Type': {'dtype': 'u4', 'offset': 56, 'bitMask': 0xF, 'bitLen': 4},
                    'Window': {'dtype': 'u4', 'offset': 35, 'bitMask': 0x1FFFFF, 'bitLen': 21},
                    'Timestamp': {'dtype': 'u4', 'offset': 13, 'bitMask': 0x3FFFFF, 'bitLen': 22},
                    'Addr': {'dtype': 'u4', 'offset': 4, 'bitMask': 0x1FF, 'bitLen': 9},
                    'Bin': {'dtype': 'u4', 'offset': 1, 'bitMask': 0x7, 'bitLen': 3},
                    'DCA': {'dtype': 'B', 'offset': 0, 'bitMask': 0x1, 'bitLen': 1}}

PLL_TDC_FRAME_FORMAT = {'Fine': {'dtype': 'u4', 'offset': 10, 'bitMask': 0x3FF, 'bitLen': 10},
                        'Coarse': {'dtype': 'u4', 'offset': 0, 'bitMask': 0x3FF, 'bitLen': 10}}

RAW_TIMESTAMP_FRAME_FORMAT_WRAW = {'RAW': {'dtype': 'u8', 'offset': 0, 'bitMask': 0xFFFFFFFFFFFFFFFF, 'bitLen': 64},
                                   'RESERVED': {'dtype': 'u4', 'offset': 53, 'bitMask': 0x7FF, 'bitLen': 11},
                                   'CorrBit': {'dtype': 'B', 'offset': 52, 'bitMask': 0x01, 'bitLen': 1},
                                   'Coarse': {'dtype': 'u4', 'offset': 48, 'bitMask': 0xF, 'bitLen': 4},
                                   'Fine': {'dtype': 'u4', 'offset': 38, 'bitMask': 0x3FF, 'bitLen': 10},
                                   'Global': {'dtype': 'u4', 'offset': 17, 'bitMask': 0x1FFFFF, 'bitLen': 21},
                                   'Energy': {'dtype': 'u4', 'offset': 9, 'bitMask': 0xFF, 'bitLen': 8},
                                   'Addr': {'dtype': 'u4', 'offset': 0, 'bitMask': 0x1FF, 'bitLen': 9}}

PROCESSED_TIMESTAMP_FRAME_FORMAT_WRAW = {
    'RAW': {'dtype': 'u8', 'offset': 0, 'bitMask': 0xFFFFFFFFFFFFFFFF, 'bitLen': 64},
    'RESERVED': {'dtype': 'u4', 'offset': 55, 'bitMask': 0x1FF, 'bitLen': 9},
    'Timestamp': {'dtype': 'u8', 'offset': 17, 'bitMask': 0xFFFFFFFFFF, 'bitLen': 38},
    'Energy': {'dtype': 'u4', 'offset': 9, 'bitMask': 0xFF, 'bitLen': 8},
    'Addr': {'dtype': 'u4', 'offset': 0, 'bitMask': 0x1FF, 'bitLen': 9}}

QKD_FRAME_FORMAT_WRAW = {'RAW': {'dtype': 'u8', 'offset': 0, 'bitMask': 0xFFFFFFFFFFFFFFFF, 'bitLen': 64},
                         'Parity': {'dtype': 'B', 'offset': 63, 'bitMask': 0x1, 'bitLen': 1},
                         'Message_Type': {'dtype': 'u4', 'offset': 60, 'bitMask': 0x7, 'bitLen': 3},
                         'PP_Type': {'dtype': 'u4', 'offset': 56, 'bitMask': 0xF, 'bitLen': 4},
                         'Window': {'dtype': 'u4', 'offset': 35, 'bitMask': 0x1FFFFF, 'bitLen': 21},
                         'Timestamp': {'dtype': 'u4', 'offset': 13, 'bitMask': 0x3FFFFF, 'bitLen': 22},
                         'Addr': {'dtype': 'u4', 'offset': 4, 'bitMask': 0x1FF, 'bitLen': 9},
                         'Bin': {'dtype': 'u4', 'offset': 1, 'bitMask': 0x7, 'bitLen': 3},
                         'DCA': {'dtype': 'B', 'offset': 0, 'bitMask': 0x1, 'bitLen': 1}}

PLL_TDC_FRAME_FORMAT_WRAW = {'RAW': {'dtype': 'u8', 'offset': 0, 'bitMask': 0xFFFFFFFFFFFFFFFF, 'bitLen': 64},
                             'Fine': {'dtype': 'u4', 'offset': 10, 'bitMask': 0x3FF, 'bitLen': 10},
                             'Coarse': {'dtype': 'u4', 'offset': 0, 'bitMask': 0x3FF, 'bitLen': 10}}



##############################


def getFrameFormat(self, num, keepRaw=False):
    if num == 0:
        format_reverse_bits = False
        if keepRaw:
            return RAW_TIMESTAMP_FRAME_FORMAT_WRAW, format_reverse_bits
        else:
            return RAW_TIMESTAMP_FRAME_FORMAT, format_reverse_bits
    elif num == 1:
        format_reverse_bits = True
        if keepRaw:
            return PLL_TDC_FRAME_FORMAT_WRAW, format_reverse_bits
        else:
            return PLL_TDC_FRAME_FORMAT, format_reverse_bits
    elif num == 2:
        format_reverse_bits = False
        if keepRaw:
            return PROCESSED_TIMESTAMP_FRAME_FORMAT_WRAW, format_reverse_bits
        else:
            return PROCESSED_TIMESTAMP_FRAME_FORMAT, format_reverse_bits
    elif num == 3:
        format_reverse_bits = False
        if keepRaw:
            return QKD_FRAME_FORMAT_WRAW, format_reverse_bits
        else:
            return QKD_FRAME_FORMAT, format_reverse_bits
    else:
        return -1


def getFrameDtype(self, num, keepRaw=False):
    if num == 0:
        if keepRaw:
            return RAW_TIMESTAMP_FRAME_DTYPE_WRAW
        else:
            return RAW_TIMESTAMP_FRAME_DTYPE
    elif num == 1:
        if keepRaw:
            return PLL_TDC_FRAME_DTYPE_WRAW
        else:
            return PLL_TDC_FRAME_DTYPE
    elif num == 2:
        if keepRaw:
            return PROCESSED_TIMESTAMP_FRAME_DTYPE_WRAW
        else:
            return PROCESSED_TIMESTAMP_FRAME_DTYPE
    elif num == 3:
        if keepRaw:
            return QKD_FRAME_DTYPE_WRAW
        else:
            return QKD_FRAME_DTYPE
    else:
        return -1