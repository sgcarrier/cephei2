import h5py
import logging
import numpy as np
from scipy import stats

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing, findTrueMaxFineWThreshold

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

    def hist_norm(self, filename, basePath, formatNum, tdcNums):
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
    BH.hist_norm(filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_07/raw_data/18oct2021/NON_CORR_ALL_DAC_M1_D500.hdf5",
                 basePath="auto",
                 formatNum=0,
                 tdcNums=[8,9,10,11,12])
    # Actually display
    plt.show()