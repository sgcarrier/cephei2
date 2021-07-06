import h5py
import logging
import numpy as np
from scipy import stats

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import post_processing, findTrueMaxFineWThreshold
from tqdm import tqdm

_logger = logging.getLogger(__name__)

class SPTRGraph():

    def convert2SimpleTimestamp(self, data, maxCoarse=8,maxFine=50):
        LSB = 4000/(maxFine*maxCoarse) # in ps
        ts = ((data['Global'] * 4000) + (data['Coarse']*data['Fine']*LSB)).astype('int64') # in ps
        return ts

    def SPTR_plot(self, filename, basePath, formatNum, spadTDCAddr, refTDCAddr):
        _logger.info("Generating count plot")
        with h5py.File(filename, "r") as h: #The file is only open as long as we are within this clause, it closes itself
            # Get the data pointer
            ds = h[basePath][:40000000]
            ds = ds[((ds['Addr'] == (spadTDCAddr)) | (ds['Addr'] == (refTDCAddr)))]

            ds = ds[ds['Coarse'] < 9]

            spadTDC_global = np.array(ds["Global"])[ds['Addr'] == (spadTDCAddr)]

            maxFineSPADTDC = np.max(np.array(ds["Fine"])[ds['Addr'] == (spadTDCAddr)])
            maxCoarseSPADTDC = np.max(np.array(ds["Coarse"])[ds['Addr'] == (spadTDCAddr)])

            maxFineREFTDC = np.max(np.array(ds["Fine"])[ds['Addr'] == (refTDCAddr)])
            maxCoarseREFTDC = np.max(np.array(ds["Coarse"])[ds['Addr'] == (refTDCAddr)])
            #maxCoarseREFTDC = 8

            print("SPAD MAX FINE: " + str(maxFineSPADTDC))
            print("SPAD MAX Coarse: " + str(maxCoarseSPADTDC))
            print("REF MAX FINE: " + str(maxFineREFTDC))
            print("REF MAX Coarse: " + str(maxCoarseREFTDC))


            spadHitsLen = len(spadTDC_global)
            time_diff_table = np.zeros((spadHitsLen,), dtype='int64')
            curr_idx = 0

            plt.figure(1)

            for idx in tqdm(range(10,len(ds)-1)):
                if (ds[idx]['Addr'] == spadTDCAddr):
                    # Check neighboors
                    spad_ts = self.convert2SimpleTimestamp(ds[idx], maxCoarse=maxCoarseSPADTDC, maxFine=maxFineSPADTDC)
                    ref_idx = idx+1
                    #while (ds[ref_idx]['Addr'] != refTDCAddr):
                    #    ref_idx += 1
                    #    if ref_idx > (len(ds)-10):
                    #        break
                    t = ds[ref_idx]
                    if ((ds[ref_idx]['Addr'] == refTDCAddr) and (ds[ref_idx]['Energy'] < 1)):
                        ref_ts = self.convert2SimpleTimestamp(ds[ref_idx], maxCoarse=maxCoarseREFTDC, maxFine=maxFineREFTDC)
                        if spad_ts > ref_ts :
                            ref_ts += (2**21)*4000
                        #offset = (ds[ref_idx]["Global"]-1) * 12500
                        #ref_ts -= offset
                        time_diff_table[curr_idx] = ((ref_ts - spad_ts)).astype('int64')
                        curr_idx += 1

            ax = plt.subplot(1, 1, 1)

            # Create a histogram
            time_diff_table = time_diff_table[time_diff_table != 0]
            time_diff_table = time_diff_table[time_diff_table < 40000]
            #time_diff_table -= np.min(time_diff_table)
            hist_data, hist_edges = np.histogram(time_diff_table, 400)
            ax.plot(hist_edges[:-1], hist_data)

            # Figure Formatting
            ax.set_title(" SPAD TDC: " + str(spadTDCAddr) + ", REF TDC: " +str(refTDCAddr))
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))


        _logger.info("Done generating SPTR plot and closed file")


"""
    Main function starts here
"""
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    #Instanciate the class
    BH = SPTRGraph()

    #Generate the Normalized histogram
    # Filename = The file, including path, of the HDF5 data
    # BasePath = The path inside the HDF5 file were the data is
    # FormatNum :
    #             0 = Normal 64 bits no post-processing
    #             1 = PLL 20 bits
    # tdcNums = Array of tdcs addresses to display
    #"/home/simonc/Documents/DATA/data28mai/DARK/TDC_NON_CORR-20210528-172742.hdf5"
    #"/home2/cars2019/Downloads/test_all_6.hdf5"
    #"/home2/cars2019/Documents/DATA/SPADALL_M1_DARK_fast260_-8V_5000TD.hdf5"
    BH.SPTR_plot(filename="/home2/cars2019/Documents/DATA/SPTR_PRELIM2.hdf5",
                 basePath="/CHARTIER/ASIC4/TDC/M1/2_TDC_ACTIVE/PLL/FAST_258/SLOW_250/CORR/TRIG_SPAD/ADDR_8_0/RCH_1/HOLDOFF_2/RAW",
                 formatNum=0,
                 spadTDCAddr=0,
                 refTDCAddr=1)
    # Actually display
    plt.show()

    #input("Press to exit")