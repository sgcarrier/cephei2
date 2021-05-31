import h5py
import logging
import numpy as np
from scipy import stats

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing, findTrueMaxFineWThreshold

_logger = logging.getLogger(__name__)

class CountRatePlot():

    def count_plot(self, filename, basePath, formatNum, tdcNums):
        _logger.info("Generating count plot")
        with h5py.File(filename, "r") as h: #The file is only open as long as we are within this clause, it closes itself
            # Get the data pointer
            ds = h[basePath]

            for tdcNum in tdcNums:
                plt.figure(tdcNum)

                data_TDC_global= np.array(ds["Global"])[ds['Addr'] == (tdcNum)]
                data_TDC_energy = np.array(ds["Energy"])[ds['Addr'] == (tdcNum)]

                count_plot = np.zeros((len(data_TDC_global)-1,))

                for i in range(len(data_TDC_global)-1):
                    if (data_TDC_global[i+1] - data_TDC_global[i]) > 0:
                        #Convert from 4ns steps to KHz
                        count_plot[i] = data_TDC_energy[i+1] / ((data_TDC_global[i+1] - data_TDC_global[i])*4) * 1000000
                    else: # in the case that the global counter overflows
                        time_diff = (0x1FFFFF - data_TDC_global[i]) + data_TDC_global[i+1]
                        # Convert from 4ns steps to KHz
                        count_plot[i] = data_TDC_energy[i + 1] / (time_diff * 4) * 1000000

                # Figure Formatting
                ax = plt.subplot(1, 1, 1)
                ax.set_title("SPAD Count rate (KHz), TDC : " + str(tdcNum))
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))

                textstr = '\n'.join((
                    r'Samples=%.2f' % (len(data_TDC_energy),),
                    r'Avg=%.2f KHz' % (np.mean(count_plot),)))

                ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
                        verticalalignment='top')


                print(np.mean(count_plot))
                ax.plot(count_plot)

        _logger.info("Done generating count plot and closed file")


"""
    Main function starts here
"""
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    #Instanciate the class
    BH = CountRatePlot()

    #Generate the Normalized histogram
    # Filename = The file, including path, of the HDF5 data
    # BasePath = The path inside the HDF5 file were the data is
    # FormatNum :
    #             0 = Normal 64 bits no post-processing
    #             1 = PLL 20 bits
    # tdcNums = Array of tdcs addresses to display
    #"/home/simonc/Documents/DATA/data28mai/DARK/TDC_NON_CORR-20210528-172742.hdf5"
    BH.count_plot(filename="/home/simonc/Documents/DATA/data28mai/DARK/TDC_NON_CORR-20210528-172742.hdf5",
                 basePath="/CHARTIER/ASIC0/TDC/M0/1_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/SPAD/ADDR_6/RCH_12/HOLDOFF_5/RAW",
                 formatNum=0,
                 tdcNums=[25])
    # Actually display
    plt.show()

    #input("Press to exit")