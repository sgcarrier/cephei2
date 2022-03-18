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
                trueMaxCoarse = findTrueMaxCoarseWThreshold(corrected_coarse, threshold=0.01)

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
                    text = ax.text(j, i, '%.2f' % hmMaxCoarse[i, j],
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

    def heatmap_with_decimal(self, filename, basePath, formatNum, figureNum=1, numberOfTDCs=49):
        _logger.info("Generating heatmap with decimals")
        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            side = int(math.sqrt(numberOfTDCs))
            hmMaxCoarse = np.zeros((side, side))
            hmMaxFine = np.zeros((side, side))
            hmCoarse = np.zeros((side, side))
            hmResolution = np.zeros((side, side))

            for tdcNum in range(side*side):
                # Apply post processing on Coarse
                corrected_coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum)
                # Apply post processing on Fine
                corrected_fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum)

                # Find the true Maximums of Coarse and Fine
                trueMaxFine = findTrueMaxFineWThreshold(corrected_coarse, corrected_fine, threshold=0.4)
                trueMaxCoarse = findTrueMaxCoarseDecimal(corrected_coarse, threshold=0.01)
                coarseValue = findCoarseTiming(trueMaxCoarse)
                resolution = findResolution(trueMaxCoarse, trueMaxFine)

                # Populate the Heatmap array
                hmMaxCoarse[tdcNum // side][tdcNum % side] = trueMaxCoarse
                hmMaxFine[tdcNum // side][tdcNum % side] = trueMaxFine
                hmCoarse[tdcNum // side][tdcNum % side] = coarseValue
                hmResolution[tdcNum // side][tdcNum % side] = resolution

            plt.figure(figureNum)

            # Heatmap for the corrected coarse
            ax = plt.subplot(2, 2, 1)
            ax.imshow(hmMaxCoarse)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, '%.2f' % hmMaxCoarse[i, j],
                                   ha="center", va="center", color="w")
            ax.set_title("Max Coarse")

            # Heatmap for the corrected fine
            ax = plt.subplot(2, 2, 2)
            ax.imshow(hmMaxFine)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, hmMaxFine[i, j],
                                   ha="center", va="center", color="w")
            ax.set_title("Max Fine")

            # Heatmap for Coarse Value
            ax = plt.subplot(2, 2, 3)
            ax.imshow(hmResolution)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, '%.0f' % hmCoarse[i, j],
                                   ha="center", va="center", color="w")
            ax.set_title("Coarse Value (ps)")

            # Heatmap for LSB
            ax = plt.subplot(2, 2, 4)
            ax.imshow(hmResolution)
            # Loop over data dimensions and create text annotations.
            for i in range(side):
                for j in range(side):
                    text = ax.text(j, i, '%.0f' % hmResolution[i, j],
                                   ha="center", va="center", color="w")
            ax.set_title("LSB (ps)")

        _logger.info("Done Generating heatmap with decimals and closed file")

    def search_sequence_numpy(self, arr, seq):
        """ Find sequence in an array using NumPy only.

        Parameters
        ----------
        arr    : input 1D array
        seq    : input 1D array

        Output
        ------
        Output : 1D Array of indices in the input array that satisfy the
        matching of input sequence in the input array.
        In case of no match, an empty list is returned.
        """

        # Store sizes of input array and sequence
        Na, Nseq = arr.size, seq.size

        # Range of sequence
        r_seq = np.arange(Nseq)

        # Create a 2D array of sliding indices across the entire length of input array.
        # Match up with the input sequence & get the matching starting indices.
        M = (arr[np.arange(Na - Nseq + 1)[:, None] + r_seq] == seq).all(1)

        # Get the range of those indices as final output
        if M.any() > 0:
            return np.where(np.convolve(M, np.ones((Nseq), dtype=int)) > 0)[0]
        else:
            return []  # No match found

    def covariance_with_filtering(self, filename, basePath, formatNum, figureNum=1, numberOfTDCs=49):
        _logger.info("Generating covariance with filtering")
        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            side = int(math.sqrt(numberOfTDCs))
            hmMaxCoarse = np.zeros((side, side))
            hmMaxFine = np.zeros((side, side))

            SAMPLES = 50000

            timestamps = np.zeros((numberOfTDCs, SAMPLES))
            fines = np.zeros((numberOfTDCs, SAMPLES))
            coarses = np.zeros((numberOfTDCs, SAMPLES))

            maxFine = np.zeros((numberOfTDCs,))

            timestamps_x = np.zeros((numberOfTDCs, SAMPLES))

            idx  = self.search_sequence_numpy(ds["Addr"], np.array((range(0,193, 4))))

            # mask = np.zeros((len(ds["Addr"]),))
            # td = 0
            # for i in range(SAMPLES):
            #     if td == ds['Addr'][i]:
            #         mask[i] = 1
            #         td += 4
            #     else:
            #         mask[i - td:i] = [0] * ((td) // 4)
            #         td = 0
            #
            #     if td >= numberOfTDCs * 4:
            #         td = 0

            #bmask = mask != 0

            for tdcNum in range(side*side):
                # Apply post processing on Coarse
                corrected_coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum, mask=idx)
                # Apply post processing on Fine
                corrected_fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum, mask=idx)

                corrected_global = post_processing(ds, "Global", formatNum, tdcNum=tdcNum, mask=idx)

                # Find the true Maximums of Coarse and Fine
                trueMaxFine = findTrueMaxFineWThreshold(corrected_coarse, corrected_fine, threshold=0.4)
                trueMaxCoarse = findTrueMaxCoarseWThreshold(corrected_coarse, threshold=0.01)

                #Populate the Heatmap array
                hmMaxCoarse[tdcNum // side][tdcNum % side] = trueMaxCoarse
                hmMaxFine[tdcNum // side][tdcNum % side] = trueMaxFine
                print("TDC " + str(tdcNum) + " : " + str(trueMaxFine) + ", " +str(np.max(corrected_fine)))
                coarseStep = 4000 / trueMaxCoarse
                psStep = (coarseStep / trueMaxFine)
                # coarseStep = 500.0
                # psStep = 10.0

                #sync_corrected_fine = np.array([corrected_fine[i] for i in idx[:SAMPLES]])
                #sync_corrected_coarse = np.array([corrected_coarse[i] for i in idx[:SAMPLES]])


                t =(corrected_fine[:SAMPLES] * psStep) + (corrected_coarse[:SAMPLES] * coarseStep)
                timestamps[tdcNum,:SAMPLES] = t
                fines[tdcNum,:SAMPLES] = corrected_fine[:SAMPLES]
                coarses[tdcNum, :SAMPLES] = corrected_coarse[:SAMPLES]
                timestamps_x[tdcNum,:SAMPLES] = corrected_global[:SAMPLES]


            fig = plt.figure(figureNum)

            cov_mat = np.corrcoef(timestamps)
            # diff = []
            # for i in range(tdcNum):
            #     diff.append(np.mean((timestamps[0,:] - np.mean(timestamps[0,:]))*(timestamps[i,:] - np.mean(timestamps[i,:]))))

            diff = timestamps[0,:] - timestamps[42,:]

            # Heatmap for the corrected coarse
            ax = plt.subplot(1, 1, 1)
            img = ax.imshow(cov_mat)

            ax.set_xticks([0,7,14,21,28,35,42,48])
            ax.set_yticks([0,7,14,21,28,35,42,48])
            plt.xlabel("TDC num")
            plt.ylabel("TDC num")
            fig.colorbar(img)

            print()


            # fig2 = plt.figure(figureNum+1)
            # ax2 = plt.subplot(1, 1, 1)
            #
            # img = ax2.imshow(hmMaxFine)
            # ax2.set_xticks([0, 7, 14, 21, 28, 35, 42, 48])
            # ax2.set_yticks([0, 7, 14, 21, 28, 35, 42, 48])


            # ax_1 = plt.subplot(5, 1, 1)
            # ax_1.plot(timestamps_x[0,10050:10250], diff[10050:10250], 'x')
            # ax_2 = plt.subplot(5, 1, 2, sharex=ax_1)
            # ax_2.plot(timestamps_x[0, 10050:10250], fines[0,10050:10250])
            # ax_3 = plt.subplot(5, 1, 3, sharex=ax_1)
            # ax_3.plot(timestamps_x[0, 10050:10250], coarses[0, 10050:10250])
            # ax_4 = plt.subplot(5, 1, 4, sharex=ax_1)
            # ax_4.plot(timestamps_x[0, 10050:10250], fines[42, 10050:10250])
            # ax_5 = plt.subplot(5, 1, 5, sharex=ax_1)
            # ax_5.plot(timestamps_x[0, 10050:10250], coarses[42, 10050:10250])

            # Loop over data dimensions and create text annotations.
            # for i in range(side):
            #     for j in range(side):
            #         text = ax2.text(j, i, '%.2f' % hmMaxFine[i, j],
            #                        ha="center", va="center", color="w")
            ax.set_title("Covariance Matrix. Array 0, Head 5.")

        _logger.info("Done Generating covariance matrix with filtering and closed file")



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
    #BH.heatmap(filename="C:\\Users\\labm1507\\Documents\\DATA\\NON_CORR_TDC_SINGLE_TEST_12mars.hdf5",
    #           basePath="CHARTIER/ASIC0/MO/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0",
    #           formatNum=0,
    #           figureNum=1,
    #           numberOfTDCs=49)

    #BH.heatmap_with_filtering(filename="C:\\Users\\labm1507\\Documents\\DATA\\NON_CORR_TDC_SINGLE_TEST_12mars.hdf5",
    #                          basePath="CHARTIER/ASIC0/MO/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0",
    #                          formatNum=0,
    #                          figureNum=2,
    #                          numberOfTDCs=49)

    BH.covariance_with_filtering(filename="/home/simonc/Documents/DATA/1_mars_2022/H5_M0_NON_CORR_DAC.hdf5",
                            basePath="/CHARTIER/ASIC5/TDC/M0/ALL_TDC_ACTIVE/DAC/FAST_1.28/SLOW_1.263/NON_CORR/EXT/ADDR_ALL/RAW",
                            formatNum=0,
                            figureNum=3,
                            numberOfTDCs=49)

    # Actually display the graphs
    plt.show()