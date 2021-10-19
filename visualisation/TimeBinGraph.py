import h5py
import logging
import numpy as np
from scipy import stats

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing, findTrueMaxFineWThreshold

_logger = logging.getLogger(__name__)





class TimeBinGraph():

    def findBinsPerDelays(self, g, bins, postfix=''):
        delays = []
        bin0 = []
        bin1 = []
        bin2 = []
        bin3 = []
        bin4 = []
        avgTS = []
        stdTS = []
        err = []

        for key in g.keys():
            delays.append(int(key.split('_')[1]))

        for delay in delays:
            d = g["DELAY_" + str(delay) + "/" + postfix]["Bin"]
            ts = g["DELAY_" + str(delay) + "/" + postfix]["Timestamp"]
            bin0.append(len(d[d == 0]))
            bin1.append(len(d[d == 1]))
            bin2.append(len(d[d == 2]))
            bin3.append(len(d[d == 3]))
            bin4.append(len(d[d == 4]))
            avgTS.append(np.mean(ts))
            stdTS.append(np.std(ts))

            # Bin Assignement error rate
            errT = 0
            errT += sum((ts < bins[0]) != (d == 0))
            errT += sum(((ts >= bins[0]) & (ts < bins[1])) != (d == 1))
            errT += sum(((ts >= bins[1]) & (ts < bins[2])) != (d == 2))
            errT += sum(((ts >= bins[2]) & (ts < bins[3])) != (d == 3))
            errT += sum((ts >= bins[3]) != (d == 4))
            err.append(errT)



        return {'delay': delays, 'bin0': bin0, 'bin1': bin1, 'bin2': bin2, 'bin3': bin3, 'bin4': bin4, 'avgTS': avgTS, 'stdTS': stdTS, 'err': err}

    def hist_norm(self, filename, basePath, formatNum, tdcNums):
        _logger.info("Generating histogram")
        with h5py.File(filename, "r") as h: #The file is only open as long as we are within this clause, it closes itself
            # Get the data pointer
            ds = h[basePath]
            data = self.findBinsPerDelays(ds, bins=[950,1000,1050,1100], postfix="WINDOW_LEN_2/RAW")

            ax = plt.subplot(3, 1, 1)

            ax.plot(data['delay'], data['bin0'], '-o', label="Bin 0 - Out of Bounds")
            ax.plot(data['delay'], data['bin1'], '-o', label="Bin 1")
            ax.plot(data['delay'], data['bin2'], '-o', label="Bin 2")
            ax.plot(data['delay'], data['bin3'], '-o', label="Bin 3")
            ax.plot(data['delay'], data['bin4'], '-o', label="Bin 4 - Out of Bounds")
            #ax.set_xlabel("Delay (ps)")
            ax.set_ylabel("Count")
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels)
            ax.set_title("Time-Bin assignment as a function of the delay")

            ax2 = plt.subplot(3, 1, 2, sharex=ax)
            ax2.plot(data['delay'], data['avgTS'], label="Avg Timestamp")
            ax2.errorbar(data['delay'], data['avgTS'], data['stdTS'], label="Timestamps STD")
            ax2.set_title("Average Timestamp as a function of the the delay")
            #ax2.set_xlabel("Delay (ps)")
            ax2.set_ylabel("Timestamp (ps)")

            ax3 = plt.subplot(3, 1, 3, sharex=ax)
            ax3.plot(data['delay'], data['stdTS'], label="Jitter")
            ax3.set_title("Jitter per delay")
            ax3.set_xlabel("Delay (ps)")
            ax3.set_ylabel("std jitter")

            # ax4 = plt.subplot(4, 1, 4, sharex=ax)
            # ax4.plot(data['avgTS'], data['bin0'], '-o', label="Bin 0 - ERROR")
            # ax4.plot(data['avgTS'], data['bin1'], '-o', label="Bin 1")
            # ax4.plot(data['avgTS'], data['bin2'], '-o', label="Bin 2")
            # ax4.plot(data['avgTS'], data['bin3'], '-o', label="Bin 3")
            # ax4.plot(data['avgTS'], data['bin4'], '-o', label="Bin 4")
            # ax.set_xlabel("Average TS (ps)")
            # ax4.set_ylabel("Count")
            # handles, labels = ax.get_legend_handles_labels()
            # ax4.legend(handles, labels)
            # ax4.set_title("Time-Bin assignment as a function of the Average Timestamp")

"""
    Main function starts here
"""
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    #Instanciate the class
    BH = TimeBinGraph()

    #Generate the Normalized histogram
    # Filename = The file, including path, of the HDF5 data
    # BasePath = The path inside the HDF5 file were the data is
    # FormatNum :
    #             0 = Normal 64 bits no post-processing
    #             1 = PLL 20 bits
    # tdcNums = Array of tdcs addresses to display
    BH.hist_norm(filename="/home2/cars2019/Documents/DATA/TIME_BIN_WINDOW_CORR-20210727-155035.hdf5",
                 basePath="/CHARTIER/ASIC0/TDC/M0/1_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_0",
                 formatNum=0,
                 tdcNums=[0])
    # Actually display
    plt.show()