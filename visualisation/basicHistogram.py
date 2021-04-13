import h5py
import logging
import numpy as np

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing

_logger = logging.getLogger(__name__)

class BasicHistogram():

    def hist_norm(self, filename, basePath, formatNum, tdcNums):
        _logger.info("Generating histogram")
        with h5py.File(filename, "r") as h: #The file is only open as long as we are within this clause, it closes itself
            # Get the data pointer
            ds = h[basePath]

            globalCounters = np.zeros(len(ds))
            for i in range(len(ds)):
                globalCounters[i] = (ds[i] >> np.uint64(17)) & np.uint64(0x1FFFFF)

            plt.figure(1)
            ax = plt.subplot(1, 1, 1)
            ax.plot(globalCounters)

            plt.show()

            exit()

            number_of_subplots = 2 # 2 because we have fine and coarse
            for tdcNum in tdcNums:
                plt.figure(tdcNum)
                for i, v in enumerate(["Fine", "Coarse"], start=1):
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
    BH.hist_norm(filename="/home2/cars2019/Documents/DATA/NON_CORR_TEST_ALL-20210407-194310.hdf5",
                 basePath="CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL",
                 formatNum=0,
                 tdcNums=[0])

    # Actually display
    plt.show()