from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np
import h5py
import logging
import math
from matplotlib import pyplot as plt
from tqdm import tqdm
from scipy.optimize import curve_fit

from processing.ICYSHSR1_transfer_function_ideal import *
from processing.visuPostProcessing import *




class JitterCorr():

    def __init__(self):
        self.TFS = []


    def getTFs(self, filename, basePath, numberOfTDCs):

        if len(self.TFS) != 0:
            self.TFS = []

        for tdcNum in range(numberOfTDCs):
            self.TFS.append(TransferFunctions(filename=filename,
                                              basePath=basePath,
                                              pixel_id=tdcNum * 4))

    """
    The timing table is used for pretty much all steps of the correlated tests
    """
    def genTimingTable(self, filename, basePath, tdcNum):

        with h5py.File(filename, "r") as h:

            timingTable = np.empty(shape=[0, 0])
            self.total_hist = np.empty(shape=[0, 0])
            for delayPath in h[basePath].keys():
                if "DELAY_" in delayPath:
                    currDelay = int(delayPath.split('_')[1])
                    currPath = basePath + "/" + delayPath + '/RAW'

                    corrected_coarse = post_processing(h[currPath], "Coarse", 0, tdcNum=tdcNum, mask=None)
                    # Apply post processing on Fine
                    corrected_fine = post_processing(h[currPath], "Fine", 0, tdcNum=tdcNum, mask=None)

                    #Conver to code value
                    codes = [self.TFS[tdcNum].get_code(c, f) for c, f in zip(corrected_coarse, corrected_fine)]

                    maxCode = (np.sum(self.TFS[tdcNum].fine_by_coarse) + 10)

                    codeHist, _ = np.histogram(codes, bins=np.arange(0, maxCode, 1))

                    np.nan_to_num(codeHist, copy=False)

                    sumCodes = sum(codeHist)
                    if sumCodes != 0:
                        codeHistNorm = codeHist / sumCodes
                    else:
                        codeHistNorm = codeHist

                    if len(codeHistNorm) > timingTable.shape[1]:
                        timingTable.resize((timingTable.shape[0], (len(codeHistNorm))))
                        #self.total_hist.resize((self.total_hist.shape[0], (len(codeHistNorm))))
                    if currDelay >= timingTable.shape[0]:
                        timingTable.resize(((currDelay + 1), timingTable.shape[1]), refcheck=False)
                        #self.total_hist.resize(((currDelay + 1), self.total_hist.shape[1]), refcheck=False)
                    # timingTable[currDelay, :] = codeHistNorm
                    timingTable[currDelay, :] = codeHist
                    half_point = int(np.max(codes) / 2)
                    #self.total_hist[currDelay, :] = np.roll(codeHist, half_point - np.int64(np.mean(codes)))
                    #self.total_data_points = np.append(self.total_data_points, (codes - np.int64(np.mean(codes))))
        return timingTable


    def genTotalJitter(self, filename, basePath, tdcNum):


        TT = self.genTimingTable(filename,basePath,tdcNum)

        midPoint = len(TT[:,0])

        timetable_size = TT.shape[0]
        ttt = np.copy(TT[0:timetable_size, :])

        maxCode = len(ttt[0, :])

        plt.figure()
        ax = plt.subplot(1,1,1)
        ax.plot(ttt[:, 100])

        print(np.sum(ttt))

        # For every code, find the average delay, and shift so that the events are centered on the middle delay (2000ps)
        for code in range(len(ttt[0, :])):
            if np.sum(ttt[:, code]) == 0:
                continue
            avg_delay = np.average(list(range(0, timetable_size)), weights=ttt[:, code])
            avg_delay_w_step = np.floor(avg_delay / 2) * 2
            ttt[:, code] = np.roll(ttt[:, code], int(timetable_size / 2) - int(avg_delay_w_step))

        total_hist_sum = np.sum(ttt, axis=1).astype(np.int64)

        total_hist_sum_norm = total_hist_sum / np.sum(total_hist_sum)

        plt.figure(2)
        ax = plt.subplot(1, 1, 1)
        ax.bar(np.arange(len(total_hist_sum)), total_hist_sum_norm, align='center')
        # ax.bar(np.arange(len(self.total_timingTable[:, 230])), self.total_timingTable[:, 230], align='center')





        raw_data_recon = np.empty((0,))

        # for i in range(len(total_hist_sum)):
        #     raw_data_recon = np.append(raw_data_recon, [i] * (total_hist_sum[i]))

        # Curve Fitting
        def gaussian(x, mean, amplitude, standard_deviation):
            return amplitude * np.exp(- (x - mean) ** 2 / (2 * standard_deviation ** 2))

        popt, pcov = curve_fit(gaussian, list(range(0, timetable_size, 1)), total_hist_sum_norm[0:timetable_size:1],
                               p0=[(timetable_size / 2), max(total_hist_sum) * 1.5, 20])
        x_interval_for_fit = np.linspace(0, timetable_size, 10000)
        fitGaussian = gaussian(x_interval_for_fit, *popt)
        ax.plot(x_interval_for_fit, fitGaussian, label='fit', color='r')

        title = f"Single event total jitter \n Head \#{7}, ARRAY \#{0}, DAC FAST={1.278}V, SLOW={1.263}V \n STDFit={popt[2]:.2f}, "
        ax.set_title(title)
        ax.set_xlabel('Time (ps)')
        ax.set_ylabel('Occurrences')

        ax.set_xlim(1800, 2200)


        # textstr = '\n'.join((
        #     r'Samples=%.2f' % (sum(total_hist_sum),),
        #     r'STD=%.2f' % (np.std(raw_data_recon),),
        #     r'STDFit=%.2f' % (popt[2],)))
        #
        # ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
        #         verticalalignment='top')

        plt.show()




if __name__ == '__main__':
    import sys

    logging.basicConfig(level=logging.INFO)


    NON_CORR_FILE = "/home/simonc/Documents/DATA/18_mars_2022/H7_M0_DAC_NON_CORR.hdf5"
    NON_CORR_PATH = "/CHARTIER/ASIC7/TDC/M0/ALL_TDC_ACTIVE/DAC/FAST_1.278/SLOW_1.263/NON_CORR/EXT/ADDR_ALL/RAW"

    filename = "/home/simonc/Documents/DATA/18_mars_2022/H7_M0_DAC_CORR.hdf5"
    baseDatasetPath = "/CHARTIER/ASIC7/TDC/M0/ALL_TDC_ACTIVE/DAC/FAST_1.278/SLOW_1.263/CORR/EXT/ADDR_ALL/"


    JC = JitterCorr()

    JC.getTFs(NON_CORR_FILE, NON_CORR_PATH, 49)

    JC.genTotalJitter(filename, baseDatasetPath, 2)


