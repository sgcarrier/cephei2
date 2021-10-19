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


class TimingTableVisualizer:

    def __init__(self):
        self.fh = None
        self.total_data_points = np.empty((0,))
        self.total_hist = None
        self.total_timingTable = None

    def open(self, filename):
        self.fh = h5py.File(filename, 'r', libver='latest', swmr=True)




    def close(self):
        self.fh.close()

    def TDCodes(self, basePath, withFlush=True, maxFine=None, maxCoarse=None, TDCNum=0):
        lfh = self.fh[basePath]
        if maxFine:
            maxFine = np.int64(maxFine)
        else:
            maxFine = self.findReasonableMax3(lfh['Fine'], threshold=0.05, offset=2)


        if maxCoarse:
            maxCoarse = np.int64(maxCoarse)
        else:
            maxCoarse = self.findReasonableMax3(lfh['Coarse'], threshold=0.05, offset=2)


        conditionIndex = (lfh['Coarse'] < maxCoarse) & (lfh['Fine'] < maxFine ) & (lfh['Addr'] == TDCNum)

        fine = ((lfh['Fine'][:])[conditionIndex]).astype('int64')
        # if fine.size != 0:
        #     fine -= np.min(fine)
        coarse = ((lfh['Coarse'][:])[conditionIndex]).astype('int64')

        TDCCodes = (coarse * maxFine) + fine



        return TDCCodes, maxFine, maxCoarse

    def coarseZeroHist(self, basePath, TDCNum=0):

        total_data = np.empty((0, ))
        for delayPath in self.fh[basePath].keys():
            if "DELAY_" in delayPath:
                currDelay = int(delayPath.split('_')[1])
                currPath = basePath + "/" + delayPath + '/RAW'

                data = self.fh[currPath]

                dataZero = (data[(data['Coarse'] == 0) & (data['Addr'] == TDCNum)])['Fine']

                if dataZero.size != 0:
                    total_data = np.append(total_data, dataZero)

        hist_fine = np.bincount(total_data.astype("int32"))

        plt.figure(5)
        ax = plt.subplot(1, 1, 1)
        ax.bar(np.arange(len(hist_fine)), hist_fine, align='center')

        ax.set_title(" Histogram for Coarse == 0")

        ax.set_xlabel('Code')
        ax.set_ylabel('Samples')

        plt.show()





    def genDistOfCodesFile(self, basePath, maxFine=None, maxCoarse=None, TDCNum=0, nonCorrPath=None):

        if nonCorrPath:
            _, maxFine, maxCoarse = self.TDCodes(basePath=nonCorrPath,
                                                 maxFine=maxFine,
                                                 maxCoarse=maxCoarse,
                                                 TDCNum=TDCNum)

        timingTable = np.empty(shape=[0, 0])
        self.total_hist = np.empty(shape=[0, 0])
        for delayPath in self.fh[basePath].keys():
            if "DELAY_" in delayPath:
                currDelay = int(delayPath.split('_')[1])
                currPath = basePath + "/" + delayPath + '/RAW'
                codes, _, _ = self.TDCodes(basePath=currPath,
                                              maxFine=maxFine,
                                              maxCoarse=maxCoarse,
                                              TDCNum=TDCNum)
                codeHist, _ = np.histogram(codes, bins=np.arange(0, maxFine * maxCoarse, 1))

                np.nan_to_num(codeHist, copy=False)

                sumCodes = sum(codeHist)
                if sumCodes != 0:
                    codeHistNorm = codeHist / sumCodes
                else:
                    codeHistNorm = codeHist

                if len(codeHistNorm) > timingTable.shape[1]:
                    timingTable.resize((timingTable.shape[0], (len(codeHistNorm))))
                    self.total_hist.resize((self.total_hist.shape[0], (len(codeHistNorm))))
                if currDelay >= timingTable.shape[0]:
                    timingTable.resize(((currDelay + 1), timingTable.shape[1]), refcheck=False)
                    self.total_hist.resize(((currDelay + 1), self.total_hist.shape[1]), refcheck=False)
                #timingTable[currDelay, :] = codeHistNorm
                timingTable[currDelay, :] = codeHist
                half_point = int((maxFine * maxCoarse) /2)
                self.total_hist[currDelay, :] = np.roll(codeHist, half_point - np.int64(np.mean(codes)))
                self.total_data_points = np.append(self.total_data_points, (codes - np.int64(np.mean(codes))))
        return timingTable, maxFine, maxCoarse


    def showTimingTable(self, basePath, maxFine=None, maxCoarse=None, TDCNum=0, nonCorrPath=None):
        # w = gl.GLViewWidget()
        # w.opts['distance'] = 40
        # w.show()
        # w.setWindowTitle('pyqtgraph example: GLLinePlotItem')

        timingTable, maxFine, maxCoarse = self.genDistOfCodesFile(basePath=basePath,
                                                                  maxFine=maxFine,
                                                                  maxCoarse=maxCoarse,
                                                                  TDCNum=TDCNum,
                                                                  nonCorrPath=nonCorrPath)
        self.total_timingTable = timingTable
        # gx = gl.GLGridItem()
        # gx.rotate(90, 0, 1, 0)
        # gx.translate(0, 0, 0)
        # w.addItem(gx)
        # gy = gl.GLGridItem()
        # gy.rotate(90, 1, 0, 0)
        # gy.translate(0, 0, 0)
        # w.addItem(gy)
        # gz = gl.GLGridItem()
        # gz.translate(0, 0, 0)
        # w.addItem(gz)
        #
        # axis = gl.GLAxisItem()
        # # xAxis.paint()
        # # axis.setSize(self.valueNumber, self.valueNumber, self.valueNumber)
        # w.addItem(axis)

        #
        # x = np.arange(timingTable.shape[0])
        # y = np.arange(timingTable.shape[1])
        # z = timingTable / np.max(timingTable) * 10#* (10**2)
        # plt = gl.GLSurfacePlotItem(z=z, shader='normalColor')
        # w.addItem(plt)

    #
    # def showTotalHist(self):
    #     total_hist_sum = np.sum(self.total_hist, axis=0)
    #
    #     plt.figure(2)
    #     ax = plt.subplot(1, 1, 1)
    #     ax.bar(np.arange(len(total_hist_sum)), total_hist_sum, align='center')
    #
    #     ax.set_title(" Histogram TDC : 0, delay aligned, Correlated test total sum")
    #
    #     ax.set_xlabel('Code')
    #     ax.set_ylabel('Samples')
    #
    #     textstr = '\n'.join((
    #         r'Samples=%.2f' % (sum(total_hist_sum),),
    #         r'STD=%.2f' % (np.std(self.total_data_points),)))
    #
    #     ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
    #             verticalalignment='top')
    #
    #     plt.show()

    def showTotalHist(self):
        timetable_size = self.total_timingTable.shape[0]
        ttt = np.copy(self.total_timingTable[0:timetable_size, :])

        maxCode = len(ttt[0,:])

        for code in range(len(ttt[0,:])):
            if np.sum(ttt[:,code]) == 0:
                continue
            avg_delay = np.average(list(range(0, timetable_size)), weights=ttt[:,code])
            avg_delay_w_step = np.floor(avg_delay / 2) * 2
            ttt[:,code] = np.roll(ttt[:,code], int(timetable_size/2) - int(avg_delay_w_step))


        total_hist_sum = np.sum(ttt, axis=1).astype(np.int64)

        plt.figure(2)
        ax = plt.subplot(1, 1, 1)
        ax.bar(np.arange(len(total_hist_sum)), total_hist_sum, align='center')

        ax.set_title(" Histogram TDC : 0, delay aligned, Correlated test total sum")

        ax.set_xlabel('Code')
        ax.set_ylabel('Samples')


        raw_data_recon = np.empty((0,))

        for i in range(len(total_hist_sum)):
            raw_data_recon = np.append(raw_data_recon, [i]*(total_hist_sum[i]))



        # Curve Fitting
        def gaussian(x, mean, amplitude, standard_deviation):
            return amplitude * np.exp(- (x - mean) ** 2 / (2 * standard_deviation ** 2))

        popt, pcov = curve_fit(gaussian, list(range(0, timetable_size,1)), total_hist_sum[0:timetable_size:1], p0=[(timetable_size/2), max(total_hist_sum)*1.5, 20])
        x_interval_for_fit = np.linspace(0, timetable_size, 10000)
        fitGaussian = gaussian(x_interval_for_fit, *popt)
        ax.plot(x_interval_for_fit, fitGaussian, label='fit', color='r')

        textstr = '\n'.join((
            r'Samples=%.2f' % (sum(total_hist_sum),),
            r'STD=%.2f' % (np.std(raw_data_recon),),
            r'STDFit=%.2f' % (popt[2],)))

        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
                verticalalignment='top')


        plt.show()


    def jitterVsCode(self):
        ttt = np.copy(self.total_timingTable)
        size = ttt.shape[0]

        jitterRMS =  np.empty((len(ttt[0,:])))
        delayAVG =  np.empty((len(ttt[0,:])))

        for code in tqdm(range(len(ttt[0, :]))):
            raw_data_recon = np.empty((0,))

            slice = ttt[:,code]

            for i in range(len(slice)):
                raw_data_recon = np.append(raw_data_recon, [i] * int(slice[i]))

            # if (raw_data_recon.size > 0):
            #     if (np.max(raw_data_recon) - np.min(raw_data_recon) > 2000):
            #         raw_data_recon[raw_data_recon > 2000] = raw_data_recon[raw_data_recon > 2000] - 4000

            jitterRMS[code] = np.std(raw_data_recon)
            delayAVG[code] = np.mean(raw_data_recon)

        jitterRMS_noDelay = np.sqrt((jitterRMS**2) - (4.5**2))

        plt.figure(3)
        ax = plt.subplot(2, 1, 1)
        ax.plot(np.arange(len(jitterRMS_noDelay)), jitterRMS_noDelay)

        ax.set_title(" Code vs Jitter with delay line (4.5ps RMS jitter) removed")

        ax.set_xlabel('Code')
        ax.set_ylabel('Jitter RMS')

        ax2 = plt.subplot(2, 1, 2, sharex=ax)
        ax2.plot(np.arange(len(delayAVG)), delayAVG)

        ax2.set_xlabel('Code')
        ax2.set_ylabel('AVG delay')

        plt.show()



if __name__ == '__main__':
    import sys

    logging.basicConfig(level=logging.INFO)

    app = QtGui.QApplication([])

    filename = "/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_07/raw_data/18oct2021/CORR_ALL_DAC_M1_D500.hdf5"
    baseDatesetPath = "CHARTIER/ASIC7/TDC/M1/ALL_TDC_ACTIVE/DAC/FAST_1.268/SLOW_1.248/CORR/EXT/ADDR_ALL/"



    TT = TimingTableVisualizer()

    TT.open(filename=filename)

    #TT.coarseZeroHist(baseDatesetPath, TDCNum=0)

    TT.showTimingTable(baseDatesetPath, 30, 9, TDCNum=0, nonCorrPath=None)

    #TT.showTotalHist()

    TT.jitterVsCode()

    TT.close()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
