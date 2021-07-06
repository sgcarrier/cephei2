import h5py
import logging
import numpy as np
from scipy import stats

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing, findTrueMaxFineWThreshold, findTrueMaxCoarseWThreshold, findTrueMaxCoarseDecimal
from tqdm import tqdm
from scipy.optimize import curve_fit

_logger = logging.getLogger(__name__)

class SPTRWindowGraph():

    def convert2SimpleTimestamp(self, data, maxCoarse=8,maxFine=50):
        LSB = 4000/(maxFine*maxCoarse) # in ps
        ts = (((data['Coarse']*maxFine) + data['Fine'])).astype('int64')
        return ts


    def getMaxCoarseMaxFine(self, filename, basePath, formatNum, spadTDCAddr):
        with h5py.File(filename, "r") as h:
            ds = h[basePath]
            ds = ds[ds["Addr"] == (spadTDCAddr*4)]

            maxFine = findTrueMaxFineWThreshold(ds["Coarse"], ds["Fine"], 0.6)
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


"""
    Main function starts here
"""
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    #Instanciate the class
    BH = SPTRWindowGraph()


    TDC_ADDR = 1
    FORMAT = 0
    _logger.info("Going to determine the max coarse and max fine")
    maxCoarse, maxFine = BH.getMaxCoarseMaxFine(filename="/home2/cars2019/Documents/DATA/june18/NON_CORR_SPAD_EXT_1.hdf5",
                                                basePath="/CHARTIER/ASIC4/TDC/M0/1_TDC_ACTIVE/PLL/FAST_252.5/SLOW_250/NON_CORR/EXT/ADDR_1/RAW",
                                                formatNum=FORMAT,
                                                spadTDCAddr=TDC_ADDR,
                                                )

    _logger.info("Max coarse = " + str(maxCoarse))
    _logger.info("Max fine = " + str(maxFine))

    #Generate the histogram
    BH.SPTR_plot(filename="/home2/cars2019/Documents/DATA/june18/SPTR_WINDOW_TEST-20210618-194140.hdf5",
                 basePath="/CHARTIER/ASIC2/TDC/M0/1_TDC_ACTIVE/PLL/FAST_252.5/SLOW_250/CORR/SPAD/ADDR_1/RCH_1/HOLDOFF_2/DELAY_582/RAW",
                 formatNum=FORMAT,
                 spadTDCAddr=TDC_ADDR,
                 maxCoarse=maxCoarse,
                 maxFine=maxFine,
                 sampleLimit=10000000)
    # Actually display
    plt.show()

    #input("Press to exit")