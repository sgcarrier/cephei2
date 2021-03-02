import h5py
import logging
import numpy as np
import math

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

_logger = logging.getLogger(__name__)


class TDCHistogram():

    def __init__(self):
        pass

    def tdcHist(self, filename, basePath, formatNum, figureNum=1):

        _logger.info("Generating histogram")

        with h5py.File(filename, "r") as h:
            ds = h[basePath]


            plt.title(basePath)
            ax = plt.subplot(1, 1, 1)
            corrected_coarse = self.post_processing(ds, "Coarse", formatNum) # Apply post processing on Coarse
            corrected_coarse = corrected_coarse.astype('int64')

            corrected_fine = self.post_processing(ds, "Fine", formatNum)
            corrected_fine = corrected_fine.astype('int64')

            tdc_codes = (corrected_coarse * (max(corrected_fine) + 1)) + corrected_fine

            tdc_codes = tdc_codes.astype('int64')
            bins = range(min(tdc_codes), max(tdc_codes) + 4)
            ax.hist(tdc_codes, bins=list(bins))
            ax.set_title("TDC histogram: " + str(basePath))
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))


            _logger.info("reached here")
            plt.figure(figureNum)



    def post_processing(self, h, fieldName, formatNum):
        if (formatNum == 1):
            return self.post_processing_PLL_FORMAT(h, fieldName)
        else:
            return h[fieldName]

    def post_processing_PLL_FORMAT(self, h, fieldName):
        if (fieldName == "Coarse"):
            ret = (np.array(h[fieldName], dtype='int64') - (np.array(h['Fine'], dtype='int64')) + 1)
            return ret

        elif (fieldName == "Fine"):
            dat =np.array(h[fieldName], dtype='int64') - 2
            return dat

if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.DEBUG)

    BH = TDCHistogram()

    BH.tdcHist("../data_grabber/NON_CORR.hdf5", "CHARTIER/ASIC0/PLL/TDC/NON_CORR/FAST_252/SLOW_250", formatNum=1)

    plt.show()