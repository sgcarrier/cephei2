import h5py
import logging
import numpy as np
import math

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

_logger = logging.getLogger(__name__)


class BasicHistogram():

    def __init__(self):
        pass

    def hist_norm(self, filename, basePath, formatNum, figureNum=1):

        _logger.info("Generating histogram")

        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            number_of_subplots = len(ds.keys())

            plt.title(basePath)

            for i, v in enumerate(list(ds.keys()), start=1):
                ax = plt.subplot(number_of_subplots, 1, i)
                data = self.post_processing(ds, v, formatNum)
                data = data.astype('int64')
                #hist = np.bincount(data.astype('int64'))
                #ax.bar(np.arange(len(hist)), hist, align='center')
                print(min(data))
                bins = range(min(data), max(data)+2)
                ax.hist(data, bins=list(bins))
                ax.set_title(v)
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))

            _logger.info("reached here")
            plt.figure(figureNum)



    def post_processing(self, h, fieldName, formatNum):
        if (formatNum == 1):
            return self.post_processing_PLL_FORMAT(h, fieldName)
        else:
            return h[fieldName]

    # def post_processing_PLL_FORMAT(self, h, fieldName):
    #     if (fieldName == "Coarse"):
    #         ret = (np.array(h[fieldName], dtype='int64') - (np.array(h['Fine'], dtype='int64') - 2))
    #         return ret
    #
    #     elif (fieldName == "Fine"):
    #         dat =np.array(h[fieldName], dtype='int64') - 2
    #         return dat

    def post_processing_PLL_FORMAT(self, h, fieldName):
        if (fieldName == "Coarse"):
            ret = (np.array(h[fieldName], dtype='int64') - np.array(h['Fine'], dtype='int64'))
            return h[fieldName][ret == -1]

        else:
            ret = (np.array(h["Coarse"], dtype='int64') - np.array(h['Fine'], dtype='int64'))
            dat =np.array(h[fieldName], dtype='int64')
            return dat[ret == -1]

if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.DEBUG)

    BH = BasicHistogram()

    BH.hist_norm("../data_grabber/NON_CORR.hdf5", "CHARTIER/ASIC0/PLL/TDC/NON_CORR/FAST_252/SLOW_250", formatNum=1)

    plt.show()