import h5py
import logging
import numpy as np
from scipy import stats

import matplotlib
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator


from processing.visuPostProcessing import post_processing, findTrueMaxFineWThreshold
from processing.ICYSHSR1_transfer_function_ideal import *


_logger = logging.getLogger(__name__)


def h5py_dataset_iterator(g, prefix=''):
    for key in g.keys():
        item = g[key]
        path = '{}/{}'.format(prefix, key)
        if isinstance(item, h5py.Dataset): # test for dataset
            yield (path, item)
        elif isinstance(item, h5py.Group): # test for group (go down)
            yield from h5py_dataset_iterator(item, path)

class BasicHistogram():

    def hist_norm(self, filename, basePath, formatNum, tdcNums, title=None):
        _logger.info("Generating histogram")
        with h5py.File(filename, "r") as h: #The file is only open as long as we are within this clause, it closes itself
            for (path, dset) in h5py_dataset_iterator(h):
                first_path  = path
                break
            # Get the data pointer
            ds = h[first_path]
            columns = ["Coarse", "Fine"]
            number_of_subplots = len(columns) # 2 because we have fine and coarse
            for tdcNum in tdcNums:
                fig = plt.figure(tdcNum, figsize=(10,10))
                if title is not None:
                    fig.suptitle(title)
                for i, v in enumerate(columns, start=1):
                    ax = plt.subplot(number_of_subplots, 1, i)

                    # Get the data after applying post processing
                    data = post_processing(ds, v, formatNum, (tdcNum))
                    data = data.astype('int64')

                    #Create a histogram
                    hist_data = np.bincount(data)
                    ax.bar(np.arange(len(hist_data)), (hist_data/len(data)), align='center')

                    # Figure Formatting
                    ax.set_title(v + " counter value")
                    ax.xaxis.set_major_locator(MaxNLocator(integer=True))



                    maxValue = np.max(data)

                    # textstr = '\n'.join((
                    #     r'Samples=%.2f' % (len(data),),
                    #     r'MaxValue=%.2f' % (maxValue,)))
                    #
                    # ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
                    #         verticalalignment='top')

                # Apply post processing on Coarse
                corrected_coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)
                corrected_coarse = corrected_coarse.astype('int64')
                # Apply post processing on Fine
                corrected_fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)
                corrected_fine = corrected_fine.astype('int64')

                coarseZeroFine = corrected_fine[corrected_coarse == 0]

                th = 0.05
                if (coarseZeroFine.size != 0):
                    ax.axvline(stats.mode(coarseZeroFine)[0], color='r', label="Zero Mode")
                    ax.axvline(int(np.mean(coarseZeroFine)), color='b', label="Zero Mean")
                    ax.axvline((findTrueMaxFineWThreshold(corrected_coarse, corrected_fine, th)), color='g', label=f"Threshold={th}")

                plt.legend(loc='upper right')

        _logger.info("Done generating histogram and closed file")

    def hist_from_transfer_function(self, filename, basePath, formatNum, tdcNums):
        _logger.info("Generating histogram")
        with h5py.File(filename, "r") as h: #The file is only open as long as we are within this clause, it closes itself
            for (path, dset) in h5py_dataset_iterator(h):
                first_path  = path
                break
            # Get the data pointer
            ds = h[first_path]
            columns = ["Coarse", "Fine"]
            number_of_subplots = len(columns) # 2 because we have fine and coarse
            for tdcNum in tdcNums:
                plt.figure(tdcNum)
                for i, v in enumerate(columns, start=1):
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
                    ax.axvline((findTrueMaxFineWThreshold(corrected_coarse, corrected_fine, 0.05)), color='g')

        _logger.info("Done generating histogram and closed file")

    def wide_hist_from_transfer_function(self, filename, basePath, formatNum, tdcNum, maxFineMethod="Threshold=0.5", title=None):
        _logger.info("Generating histogram")
        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            # Apply post processing on Coarse
            corrected_coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)
            corrected_coarse = corrected_coarse.astype('int64')
            # Apply post processing on Fine
            corrected_fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)
            corrected_fine = corrected_fine.astype('int64')

            coarseZeroFine = corrected_fine[corrected_coarse == 0]

            if maxFineMethod == "Threshold=0.5":
                maxFine = findTrueMaxFineWThreshold(corrected_coarse, corrected_fine, 0.05)
            elif maxFineMethod == "ZeroMode":
                if (len(coarseZeroFine) == 0):
                    _logger.warning("No Zero Coarse values, using simplest")
                    maxFine = np.max(corrected_fine)
                    maxFineMethod = None
                else:
                    maxFine = stats.mode(coarseZeroFine)[0][0]
            elif maxFineMethod == "ZeroMean":
                if (len(coarseZeroFine) == 0):
                    _logger.warning("No Zero Coarse values, using simplest")
                    maxFine = np.max(corrected_fine)
                    maxFineMethod = None
                else:
                    maxFine = stats.mode(coarseZeroFine)[0][0]
            else:
                _logger.warning("Unrecognized maxFineMethod selected, using simplest")
                maxFine = np.max(corrected_fine)
                maxFineMethod =None



            codes = (corrected_coarse * maxFine) + corrected_fine

            fig = plt.figure(tdcNum, figsize=(10, 5))
            if maxFineMethod is not None:
                subtitle = f"Maximum Fine={maxFine}, with method {maxFineMethod}"
            else:
                subtitle = f"Maximum Fine={maxFine}"

            if title is not None:
                title = title + "\n" + subtitle
                fig.suptitle(title)

            ax = plt.subplot(1,1,1)
            # Create a histogram
            hist_data = np.bincount(codes)
            ax.bar(np.arange(len(hist_data)), (hist_data / len(codes)), align='center')

            plt.xlabel("TDC Code")
            plt.ylabel("Normed Frequency")

            for c in range(np.max(corrected_coarse)+2):
                ax.axvline(c*maxFine, color='r', linestyle='--', linewidth=0.5)
                if c < (np.max(corrected_coarse)+1):
                    ax.text((c*maxFine)+(0.5*maxFine), 0.95, f"Coarse={c}",
                            rotation=0,
                            transform=ax.get_xaxis_text1_transform(0)[0],
                            fontsize=10,
                            ha='center',
                            va='center')


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
    filename = "/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_05/raw_data/21_mars_2022/H5_M1_DAC_NON_CORR.hdf5"
    basepath = "/CHARTIER/ASIC5/TDC/M1/ALL_TDC_ACTIVE/DAC/FAST_1.28/SLOW_1.263/NON_CORR/EXT/ADDR_ALL/RAW"

    BH.wide_hist_from_transfer_function(filename=filename,
                                        basePath=basepath,
                                        formatNum=0,
                                        tdcNum=0,
                                        title="")

    # Actually display
    plt.show()