import h5py
import logging
import numpy as np
from scipy import stats

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing, findTrueMaxFineWThreshold, findTrueMaxCoarseWThreshold, findTrueMaxCoarseDecimal
from tqdm import tqdm
from scipy.optimize import curve_fit

from processing.ICYSHSR1_transfer_function_ideal import TransferFunctions

_logger = logging.getLogger(__name__)

class SPTRWindowGraph():

    def convert2SimpleTimestamp(self, data, maxCoarse=8,maxFine=50):
        LSB = 4000/(maxFine*maxCoarse) # in ps
        ts = (((data['Coarse']*maxFine) + data['Fine']) * LSB).astype('int64')
        return ts


    def getMaxCoarseMaxFine(self, filename, basePath, formatNum, spadTDCAddr):
        with h5py.File(filename, "r") as h:
            ds = h[basePath]
            ds = ds[ds["Addr"] == (spadTDCAddr*4)]

            maxFine = findTrueMaxFineWThreshold(ds["Coarse"], ds["Fine"], 0.05)
            maxCoarse = findTrueMaxCoarseDecimal(ds["Coarse"], 0.1)

            return maxCoarse, maxFine

    def SPTR_plot(self, filename, basePath, formatNum, spadTDCAddr, maxCoarse, maxFine, sampleLimit):
        _logger.info("Generating count plot")
        with h5py.File(filename, "r") as h: #The file is only open as long as we are within this clause, it closes itself
            # Get the data pointer
            ds = h[basePath][:sampleLimit]

            timestamps = np.zeros((len(ds),), dtype='int64')

            plt.figure(1)

            for idx in tqdm(range(0,len(ds)-1)):
                if (ds[idx]['Addr'] == (spadTDCAddr*4)):
                    timestamps[idx] = self.convert2SimpleTimestamp(ds[idx], maxCoarse=maxCoarse, maxFine=maxFine)

            ax = plt.subplot(1, 1, 1)

            # Create a histogram
            timestamps = timestamps[timestamps != 0]
            #time_diff_table -= np.min(time_diff_table)
            #hist_data, hist_edges = np.histogram(timestamps, max(timestamps)+1)
            hist_data = np.bincount(timestamps)
            #ax.bar(hist_edges[:-1], hist_data, align='center')
            x = list(range(int(max(timestamps)+1)))
            ax.bar(x, hist_data, align='center')
            # Figure Formatting
            ax.set_title(" Single Photon Timing Resolution of a single SPAD Dalsa wirebonded externally")
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))

            # Curve Fitting
            def gaussian(x, mean, amplitude, standard_deviation):
                return amplitude * np.exp(- (x - mean) ** 2 / (2 * standard_deviation ** 2))

            t = np.argmax(hist_data)
            t2  = max(hist_data) * 1.5
            popt, pcov = curve_fit(gaussian, x, hist_data,
                                   p0=[np.argmax(hist_data), max(hist_data) * 1.5, 50])
            x_interval_for_fit = np.linspace(0, x, 10000)
            fitGaussian = gaussian(x_interval_for_fit, *popt)
            ax.plot(x_interval_for_fit, fitGaussian, label='fit', color='r')

            raw_data_recon = np.empty((0,))

            for i in range(len(hist_data)):
                raw_data_recon = np.append(raw_data_recon, [i] * (hist_data[i]))

            LSB = (4000/(maxCoarse*maxFine))

            textstr = '\n'.join((
                r'Samples=%.2f' % (sum(hist_data),),
                r'STD=%.2f' % (np.std(raw_data_recon),),
                r'STDFit=%.2f' % (popt[2],),
                r'STDFit(ps)=%.2f' % (popt[2]*LSB,),
                r'FWHMFit(ps)=%.2f' % (popt[2]*LSB*2.355,)))

            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
                    verticalalignment='top')


            plt.xlabel(r'TDC code. LSB= %.2f' % LSB)
            plt.ylabel("Samples")


        _logger.info("Done generating SPTR plot and closed file")


    def SPTR(self, filename, basePath, formatNum, spadTDCAddr, maxCoarse, maxFine, sampleLimit):
        _logger.info("Generating count plot")

        # tf = TransferFunctions(filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_05/raw_data/22_mars_2022/H5_M1_DAC_NON_CORR_after_optical_tests.hdf5",
        #                        basePath="/CHARTIER/ASIC5/TDC/M1/ALL_TDC_ACTIVE/DAC/FAST_1.28/SLOW_1.263/NON_CORR/EXT/ADDR_ALL/RAW",
        #                        pixel_id=((spadTDCAddr // 4)*4),
        #                        filter_lower_than=0.05)

        with h5py.File(filename, "r") as h: #The file is only open as long as we are within this clause, it closes itself
            # Get the data pointer
            ds = h[basePath][:sampleLimit]

            timestamps = np.zeros((len(ds),), dtype='int64')

            for idx in tqdm(range(0,len(ds)-1)):
                if (ds[idx]['Addr'] == (spadTDCAddr)):
                    timestamps[idx] = self.convert2SimpleTimestamp(ds[idx], maxCoarse=maxCoarse, maxFine=maxFine)
                    #timestamps[idx] = tf.code_to_timestamp(ds[idx]["Coarse"], ds[idx]["Fine"])


            # Create a histogram
            timestamps = timestamps[timestamps != 0]
            #time_diff_table -= np.min(time_diff_table)
            #hist_data, hist_edges = np.histogram(timestamps, max(timestamps)+1)
            hist_data = np.bincount(timestamps)
            #ax.bar(hist_edges[:-1], hist_data, align='center')
            x = list(range(int(max(timestamps)+1)))

            # Curve Fitting
            def gaussian(x, mean, amplitude, standard_deviation):
                return amplitude * np.exp(- (x - mean) ** 2 / (2 * standard_deviation ** 2))

            t = np.argmax(hist_data)
            t2  = max(hist_data) * 1.5
            popt, pcov = curve_fit(gaussian, x, hist_data,
                                   p0=[np.argmax(hist_data), max(hist_data) * 1.5, 50])
            x_interval_for_fit = np.linspace(0, x, 10000)
            fitGaussian = gaussian(x_interval_for_fit, *popt)

            raw_data_recon = np.empty((0,))

            for i in range(len(hist_data)):
                raw_data_recon = np.append(raw_data_recon, [i] * (hist_data[i]))


        return popt


"""
    Main function starts here
"""
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    #Instanciate the class
    BH = SPTRWindowGraph()


    # TDC_ADDR = 0
    # FORMAT = 0
    # _logger.info("Going to determine the max coarse and max fine")
    # maxCoarse, maxFine = BH.getMaxCoarseMaxFine(filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_05/raw_data/22_mars_2022/H5_M1_DAC_NON_CORR_after_optical_tests.hdf5",
    #                                             basePath="/CHARTIER/ASIC5/TDC/M1/ALL_TDC_ACTIVE/DAC/FAST_1.28/SLOW_1.263/NON_CORR/EXT/ADDR_ALL/RAW",
    #                                             formatNum=FORMAT,
    #                                             spadTDCAddr=TDC_ADDR,
    #                                             )
    #
    # # maxCoarse = 9
    # # maxFine = 40
    #
    # _logger.info("Max coarse = " + str(maxCoarse))
    # _logger.info("Max fine = " + str(maxFine))
    #
    # #Generate the histogram
    # BH.SPTR_plot(filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_05/raw_data/22_mars_2022/H5_SPTR_DAC_OPT_SKEW_8v5_5F3.hdf5",
    #              basePath="/CHARITER/ASIC5/DAC/FAST_1.28/SLOW_1.263/SPTR/NON_INVERTED/P0/RAW",
    #              formatNum=FORMAT,
    #              spadTDCAddr=TDC_ADDR,
    #              maxCoarse=maxCoarse,
    #              maxFine=maxFine,
    #              sampleLimit=-1)
    # # Actually display
    # plt.show()

    #input("Press to exit")




    skew_map = np.zeros((8,8))

    for i in range(64):
        _logger.info("Going to determine the max coarse and max fine")
        maxCoarse, maxFine = BH.getMaxCoarseMaxFine(
            filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_05/raw_data/22_mars_2022/H5_M1_DAC_NON_CORR_after_optical_tests.hdf5",
            basePath="/CHARTIER/ASIC5/TDC/M1/ALL_TDC_ACTIVE/DAC/FAST_1.28/SLOW_1.263/NON_CORR/EXT/ADDR_ALL/RAW",
            formatNum=0,
            spadTDCAddr=(i // 4),
            )


        # _logger.info("Max coarse = " + str(maxCoarse))
        # _logger.info("Max fine = " + str(maxFine))

        path = "/CHARITER/ASIC5/DAC/FAST_1.28/SLOW_1.263/SPTR/NON_INVERTED/P" + str(i) + "/RAW"

        popt = BH.SPTR(
                filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_05/raw_data/22_mars_2022/H5_SPTR_DAC_OPT_SKEW_8v5_5F3.hdf5",
                basePath=path,
                formatNum=0,
                spadTDCAddr=i,
                maxCoarse=maxCoarse,
                maxFine=maxFine,
                sampleLimit=-1)

        tdc = i // 4
        sub = i % 4

        x_pos = (2 * tdc) % 8 + (sub % 2)
        if (sub < 2):
            y_pos = ((tdc) // (8 // 2)) * 2
        else:
            y_pos = ((tdc) // (8 // 2)) * 2 + 1
        skew_map[x_pos, y_pos] = popt[0]

    #skew_map -= np.min(skew_map)
    print(skew_map)

    plt.figure(1)
    ax = plt.subplot(1, 1, 1)
    ax.imshow(skew_map)

    plt.show()
