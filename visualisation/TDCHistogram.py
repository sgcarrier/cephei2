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

            for i in [ 13]:
                plt.figure(i)
                plt.title(basePath + "TDC : " + str(i))
                ax = plt.subplot(1, 1, 1)
                corrected_coarse = self.post_processing(ds, "Coarse", formatNum, tdcNum=i) # Apply post processing on Coarse
                corrected_coarse = corrected_coarse.astype('int64')

                corrected_fine = self.post_processing(ds, "Fine", formatNum, tdcNum=i)
                corrected_fine = corrected_fine.astype('int64')

                tdc_codes = (corrected_coarse * (max(corrected_fine) + 5)) + corrected_fine

                hist_codes = np.bincount(tdc_codes)
                ax.bar(np.arange(len(hist_codes)), hist_codes, align='center')

                #tdc_codes = tdc_codes.astype('int64')
                #bins = range(min(tdc_codes), max(tdc_codes) + 4)
                #ax.hist(tdc_codes, bins=list(bins))
                ax.set_title("ALL TDC  ACTIVE histogram: " + str(basePath) + "TDC : " + str(i))
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))





    def post_processing(self, h, fieldName, formatNum, tdcNum):
        if (formatNum == 1):
            return self.post_processing_PLL_FORMAT(h, fieldName)
        else:
            mask = np.array(h['Addr'], dtype='int64')
            return np.array(h[fieldName], dtype='int64')[mask == (tdcNum*4)]
            #return np.array(h[fieldName], dtype='int64')

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

    BH.tdcHist("../data_grabber/NON_CORR_TDC_mar3_single_kek.hdf5", "CHARTIER/ASIC0/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0/ADDR_13",formatNum=0)

    plt.show()