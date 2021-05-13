import h5py
import logging
import numpy as np
from scipy import stats

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing, findTrueMaxFineWThreshold

_logger = logging.getLogger(__name__)

class TDCHistogram():

    def tdcHist(self, filename, basePath, formatNum, tdcNums):

        _logger.info("Generating histogram")

        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            maxFine = []
            coarseZeroMinimum = []
            coarseZeroAvg = []
            coarseZeroMode = []
            maxFinewThresh = []
            x = []

            for tdcNum in tdcNums:
                # Apply post processing on Coarse
                corrected_coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)
                corrected_coarse = corrected_coarse.astype('int64')
                # Apply post processing on Fine
                corrected_fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)
                corrected_fine = corrected_fine.astype('int64')


                coarseZeroFine = corrected_fine[corrected_coarse == 0]

                if (coarseZeroFine.size != 0):

                    maxFine.append(max(corrected_fine))
                    coarseZeroMinimum.append(min(coarseZeroFine))
                    coarseZeroAvg.append(np.mean(coarseZeroFine))
                    coarseZeroMode.append(stats.mode(coarseZeroFine)[0])
                    maxFinewThresh.append(findTrueMaxFineWThreshold(corrected_coarse, corrected_fine, 0.4))

                    x.append(tdcNum)

            #Setup Plot Figure
            plt.figure(1)
            plt.title(basePath + "TDC : ")
            ax = plt.subplot(1, 1, 1)
            ax.set_title("Finding an accurate max Fine")
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))

            ax.plot(x, maxFine, marker='^', label='Max fine, no processing')
            ax.plot(x, coarseZeroMinimum, marker='v', label='Minimum in coarse zero')
            ax.plot(x, coarseZeroAvg, marker='.', label='Coarse zero average')
            ax.plot(x, coarseZeroMode, marker='s', label='Coarse zero mode')
            ax.plot(x, maxFinewThresh, marker='+', label='Max fine, with threshold')

            ax.legend()

            plt.show()

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
    BH.tdcHist(filename="/home2/cars2019/Documents/DATA/NON_CORR_TEST_ALL-20210407-194310.hdf5",
               basePath="CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/PROCESSED",
               formatNum=0,
               tdcNums=list(range(49)))

    #NeverForgetti
    plt.show()