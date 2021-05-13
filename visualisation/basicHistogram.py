import h5py
import logging
import numpy as np
from scipy import stats

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing, findTrueMaxFineWThreshold

_logger = logging.getLogger(__name__)

class BasicHistogram():

    def hist_norm(self, filename, basePath, formatNum, tdcNums):
        _logger.info("Generating histogram")
        with h5py.File(filename, "r") as h: #The file is only open as long as we are within this clause, it closes itself
            # Get the data pointer
            ds = h[basePath]

            number_of_subplots = 2 # 2 because we have fine and coarse
            for tdcNum in tdcNums:
                plt.figure(tdcNum)
                for i, v in enumerate(["Coarse", "Fine"], start=1):
                    ax = plt.subplot(number_of_subplots, 1, i)

                    # Get the data after applying post processing
                    data = post_processing(ds, v, formatNum, (tdcNum))
                    data = data.astype('int64')

                    #Create a histogram
                    hist_data = np.bincount(data)
                    ax.bar(np.arange(len(hist_data)), hist_data, align='center')

                    # Figure Formatting
                    ax.set_title(v + " TDC : " + str(tdcNum))
                    ax.xaxis.set_major_locator(MaxNLocator(integer=True))



                    maxValue = np.max(data)

                    textstr = '\n'.join((
                        r'Samples=%.2f' % (len(data),),
                        r'MaxValue=%.2f' % (maxValue,)))

                    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
                            verticalalignment='top')

                # Apply post processing on Coarse
                corrected_coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)
                corrected_coarse = corrected_coarse.astype('int64')
                # Apply post processing on Fine
                corrected_fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)
                corrected_fine = corrected_fine.astype('int64')

                coarseZeroFine = corrected_fine[corrected_coarse == 0]

                if (coarseZeroFine.size != 0):
                    ax.axvline(stats.mode(coarseZeroFine)[0], color='r')
                    ax.axvline(int(np.mean(coarseZeroFine)), color='b')
                    ax.axvline((findTrueMaxFineWThreshold(corrected_coarse, corrected_fine, 0.4)), color='g')

        _logger.info("Done generating histogram and closed file")


"""
    Main function starts here
"""
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    #Instanciate the class
    BH = BasicHistogram()

    #Generate the Normalized histogram
    # Filename = The file, including path, of the HDF5 data
    # BasePath = The path inside the HDF5 file were the data is
    # FormatNum :
    #             0 = Normal 64 bits no post-processing
    #             1 = PLL 20 bits
    # tdcNums = Array of tdcs addresses to display
    BH.hist_norm(filename="C:\\Users\\labm1507\\Documents\\DATA\\TDC_M0_NON_CORR_All-20210423-174203.hdf5",
                 basePath="/CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_252.5/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW",
                 formatNum=0,
                 tdcNums=list(range(49)))
    # Actually display
    plt.show()