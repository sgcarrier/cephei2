import h5py
import logging
import numpy as np

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing

_logger = logging.getLogger(__name__)

class TDCHistogram():

    def tdcHist(self, filename, basePath, formatNum, tdcNums):

        _logger.info("Generating histogram")

        with h5py.File(filename, "r") as h:
            ds = h[basePath]

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
    BH.tdcHist(filename="../data_grabber/NON_CORR_TDC_mar3_single_kek.hdf5",
               basePath="CHARTIER/ASIC0/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0",
               formatNum=0,
               tdcNums=[0])

    #NeverForgetti
    plt.show()