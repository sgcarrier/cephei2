import h5py
import logging
import numpy as np

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing, findMatchingTDCEvents

_logger = logging.getLogger(__name__)

class TDCHistogram():

    def tdcHist(self, filename, basePath, formatNum, tdcNums):

        _logger.info("Generating histogram")

        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            data1, data2 = findMatchingTDCEvents(tdc1Num=0, tdc2Num=4, data=ds)

            # print(data1[0])
            # print(data2[0])
            # print(data1[100])
            # print(data2[100])
            # print(data1[10000])
            # print(data2[10000])
            # exit()

            for tdcNum in tdcNums:
                #Setup Plot Figure
                plt.figure(tdcNum)
                plt.title(basePath + "TDC : " + str(tdcNum))
                ax = plt.subplot(1, 1, 1)
                ax.set_title("TDC histogram: " + str(basePath) + "TDC : " + str(tdcNum))
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))

                # Apply post processing on Coarse
                corrected_coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)
                corrected_coarse = corrected_coarse.astype('int64')
                # Apply post processing on Fine
                corrected_fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)
                corrected_fine = corrected_fine.astype('int64')

                # Calculate the codes with a buffer between them to distinctly see the different coarses
                buffer = 5
                tdc_codes = (corrected_coarse * (max(corrected_fine) + buffer)) + corrected_fine

                # Generate the histogram
                hist_codes = np.bincount(tdc_codes)
                ax.bar(np.arange(len(hist_codes)), hist_codes, align='center')

        _logger.info("Done generating histogram and closed file")


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    # Instanciate the class
    BH = TDCHistogram()

    # Filename = The file, including path, of the HDF5 data
    # BasePath = The path inside the HDF5 file were the data is
    # FormatNum :
    #             0 = Normal 64 bits no post-processing
    #             1 = PLL 20 bits
    # tdcNums = Array of tdcs addresses to display
    BH.tdcHist(filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_07/raw_data/18oct2021/NON_CORR_ALL_DAC_M1_D500.hdf5",
               basePath="/CHARTIER/ASIC7/TDC/M1/ALL_TDC_ACTIVE/DAC/FAST_1.268/SLOW_1.248/NON_CORR/EXT/ADDR_ALL/RAW",
               formatNum=0,
               tdcNums=[11])

    #NeverForgetti
    plt.show()