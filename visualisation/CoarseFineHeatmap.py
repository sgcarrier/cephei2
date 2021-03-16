import h5py
import logging
import numpy as np
import math

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

_logger = logging.getLogger(__name__)


class CoarseFineHeatmap():

    def __init__(self):
        pass

    def findTrueMaxFine(self, coarse_data, fine_data, threshold):
        trueMaxCoarse = self.findTrueMaxCoarse(coarse_data, threshold=0.1)

        hist_fine = np.bincount(fine_data[coarse_data <= trueMaxCoarse])
        for f in range(int(max(fine_data)/2), max(fine_data)):
            if hist_fine[f] < (max(hist_fine)*threshold):
                return f-1

        return max(fine_data)

    def findTrueMaxCoarse(self, coarse_data, threshold):
        hist_coarse = np.bincount(coarse_data)
        for c in range(1, max(coarse_data)):
            if hist_coarse[c] < (np.mean(hist_coarse)*threshold):
                return c-1
        return max(coarse_data)

    def heatmap(self, filename, basePath, formatNum, figureNum=1):

        _logger.info("Generating histogram")

        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            number_of_subplots = len(ds.keys())
            number_of_subplots =2

            side=7
            hmMaxCoarse = np.zeros((side, side))
            hmMaxFine = np.zeros((side, side))

            for tdcNum in range(side*side):
                corrected_coarse = self.post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)  # Apply post processing on Coarse
                corrected_fine = self.post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)

                hmMaxCoarse[tdcNum//side][tdcNum%side] = max(corrected_coarse)
                hmMaxFine[tdcNum // side][tdcNum % side] = max(corrected_fine)

            plt.figure(figureNum)


            ax = plt.subplot(2, 1, 1)
            ax.imshow(hmMaxCoarse)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, hmMaxCoarse[i, j],
                                   ha="center", va="center", color="w")

            ax.set_title("Max Coarse")

            ax = plt.subplot(2, 1, 2)
            ax.imshow(hmMaxFine)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, hmMaxFine[i, j],
                                   ha="center", va="center", color="w")

            ax.set_title("Max Fine")


    def heatmap_with_filtering(self, filename, basePath, formatNum, figureNum=1):

        _logger.info("Generating histogram")

        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            number_of_subplots = len(ds.keys())
            number_of_subplots =2

            side=7
            hmMaxCoarse = np.zeros((side, side))
            hmMaxFine = np.zeros((side, side))

            for tdcNum in range(side*side):
                corrected_coarse = self.post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)  # Apply post processing on Coarse
                corrected_fine = self.post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)

                trueMaxFine = self.findTrueMaxFine(corrected_coarse, corrected_fine, 0.4)
                trueMaxCoarse = self.findTrueMaxCoarse(corrected_coarse, 0.1)

                hmMaxCoarse[tdcNum // side][tdcNum % side] = trueMaxCoarse
                hmMaxFine[tdcNum // side][tdcNum % side] = trueMaxFine

            plt.figure(figureNum)


            ax = plt.subplot(2, 1, 1)
            ax.imshow(hmMaxCoarse)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, hmMaxCoarse[i, j],
                                   ha="center", va="center", color="w")

            ax.set_title("Max Coarse")

            ax = plt.subplot(2, 1, 2)
            ax.imshow(hmMaxFine)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, hmMaxFine[i, j],
                                   ha="center", va="center", color="w")

            ax.set_title("Max Fine")



    def post_processing(self, h, fieldName, formatNum, tdcNum):
        if (formatNum == 1):
            return self.post_processing_PLL_FORMAT(h, fieldName)
        else:
            mask = np.array(h['Addr'], dtype='int64')
            return np.array(h[fieldName], dtype='int64')[mask == (tdcNum*4)]

    def post_processing_PLL_FORMAT(self, h, fieldName):
        if (fieldName == "Coarse"):
            ret = (np.array(h[fieldName], dtype='int64') - (np.array(h['Fine'], dtype='int64') - 2))
            return ret

        elif (fieldName == "Fine"):
            dat =np.array(h[fieldName], dtype='int64') - 2
            return dat

if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.DEBUG)

    BH = CoarseFineHeatmap()

    BH.heatmap("../data_grabber/NON_CORR_TDC_mar3_ALL_20min.hdf5", "CHARTIER/ASIC0/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0", formatNum=0)

    BH.heatmap_with_filtering("../data_grabber/NON_CORR_TDC_mar3_ALL_20min.hdf5", "CHARTIER/ASIC0/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0", formatNum=0, figureNum=2)


    plt.show()