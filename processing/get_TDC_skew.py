# coding=utf-8
import h5py
import pickle
import numpy as np


def main():
    # ARR 0
    # Fichier Pascal
    #filename = "./data/ARR0/SkewCorr/TDC_M0_NON_CORR_TIME_All-20210616-132953.hdf5"
    filename = "h5_skew_data.hdf5"
    #path = "CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW"
    path = "CHARTIER/ASIC5/TDC/M1/ALL_TDC_ACTIVE/DAC/FAST_1.28/SLOW_1.263/NON_CORR/EXT/ADDR_ALL/RAW"

    calcSkewCoef(filename, path, "H5_skew_data.pickle")

def calcSkewCoef(filename, path, outputName):

    with h5py.File(filename, "r") as h:
        data = np.array(h[path])
        timestamps = np.zeros(16)
        diffs = []
        count = 0
        for packet in data:
            if packet == 0xAAAAAAAAAAAAAAAA:
                timestamps = np.zeros(16)
            elif packet == 0xAAAAAAABAAAAAAAB:
                if timestamps.all():
                    diffs.append(timestamps[0]- timestamps)
                    count +=1
                    if count > 100000:
                        break
            elif packet == 327680:
                pass
            elif packet == 327681:
                pass
            else:
                address = np.bitwise_and(packet.astype(np.int), 0x1FF)
                timestamp = np.bitwise_and(np.right_shift(packet.astype(np.int), 17), 0x7FFFFFFFFF)
                timestamps[int(address/4)] = timestamp

        skew = np.mean(np.array(diffs), axis=0)
        offset_delay = np.amax(skew)
        skew_correction = -(skew - offset_delay)
        print(skew_correction)
        with open(outputName, 'wb') as f:
            pickle.dump(skew_correction, f)


#main()
