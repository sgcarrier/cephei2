import h5py
import logging
import numpy as np
import math

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import *

_logger = logging.getLogger(__name__)


class CoarseFineHeatmap():

    def heatmap(self, filename, basePath, formatNum, figureNum=1, numberOfTDCs=49):
        _logger.info("Generating heatmap")
        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            side = int(math.sqrt(numberOfTDCs))
            hmMaxCoarse = np.zeros((side, side))
            hmMaxFine = np.zeros((side, side))

            for tdcNum in range(side*side):
                # Apply post processing on Coarse
                corrected_coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)
                # Apply post processing on Fine
                corrected_fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)

                # Populate the Heatmap array
                hmMaxCoarse[tdcNum // side][tdcNum % side] = max(corrected_coarse)
                hmMaxFine[tdcNum // side][tdcNum % side] = max(corrected_fine)

            plt.figure(figureNum)

            # Heatmap for the coarse
            ax = plt.subplot(2, 1, 1)
            ax.imshow(hmMaxCoarse)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, hmMaxCoarse[i, j],
                                   ha="center", va="center", color="w")

            ax.set_title("Max Coarse")

            # Heatmap for the fine and beautiful
            ax = plt.subplot(2, 1, 2)
            ax.imshow(hmMaxFine)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, hmMaxFine[i, j],
                                   ha="center", va="center", color="w")

            ax.set_title("Max Fine")

        _logger.info("Done Generating heatmap and closed file")


    def heatmap_with_filtering(self, filename, basePath, formatNum, figureNum=1, numberOfTDCs=49):
        _logger.info("Generating heatmap with filtering")
        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            side = int(math.sqrt(numberOfTDCs))
            hmMaxCoarse = np.zeros((side, side))
            hmMaxFine = np.zeros((side, side))

            for tdcNum in range(side*side):
                # Apply post processing on Coarse
                corrected_coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)
                # Apply post processing on Fine
                corrected_fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)

                # Find the true Maximums of Coarse and Fine
                trueMaxFine = findTrueMaxFineWThreshold(corrected_coarse, corrected_fine, threshold=0.4)
                trueMaxCoarse = findTrueMaxCoarseWThreshold(corrected_coarse, threshold=0.1)

                # Populate the Heatmap array
                hmMaxCoarse[tdcNum // side][tdcNum % side] = trueMaxCoarse
                hmMaxFine[tdcNum // side][tdcNum % side] = trueMaxFine

            plt.figure(figureNum)

            # Heatmap for the corrected coarse
            ax = plt.subplot(2, 1, 1)
            ax.imshow(hmMaxCoarse)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, hmMaxCoarse[i, j],
                                   ha="center", va="center", color="w")
            ax.set_title("Max Coarse")

            # Heatmap for the corrected fine
            ax = plt.subplot(2, 1, 2)
            ax.imshow(hmMaxFine)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, hmMaxFine[i, j],
                                   ha="center", va="center", color="w")
            ax.set_title("Max Fine")

        _logger.info("Done Generating heatmap with filtering and closed file")

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    # Instanciate the class
    BH = CoarseFineHeatmap()

    # Filename = The file, including path, of the HDF5 data
    # BasePath = The path inside the HDF5 file were the data is
    # FormatNum :
    #             0 = Normal 64 bits no post-processing
    #             1 = PLL 20 bits
    BH.heatmap(filename="../data_grabber/NON_CORR_TDC_mar3_ALL_20min.hdf5",
               basePath="CHARTIER/ASIC0/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0",
               formatNum=0,
               figureNum=1,
               numberOfTDCs=49)

    BH.heatmap_with_filtering(filename="../data_grabber/NON_CORR_TDC_mar3_ALL_20min.hdf5",
                              basePath="CHARTIER/ASIC0/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0",
                              formatNum=0,
                              figureNum=2,
                              numberOfTDCs=49)

    # Actually display the graphs
    plt.show()