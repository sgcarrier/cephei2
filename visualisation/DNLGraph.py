import h5py
import logging
import numpy as np
import math

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

_logger = logging.getLogger(__name__)


class DNLGraph():

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


    def DNL_no_jitter_cleanup(self, filename, basePath, formatNum, TDCNum, figureNum=1):

        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            plt.figure(figureNum)
            title_string = "DNL for TDC# " + str(TDCNum)
            plt.title(title_string + "\n" +basePath, fontsize=10)
            ax = plt.subplot(1, 1, 1)

            corrected_coarse = self.post_processing(ds, "Coarse", formatNum, TDCNum) # Apply post processing on Coarse

            corrected_fine = self.post_processing(ds, "Fine", formatNum, TDCNum)

            trueMaxFine = self.findTrueMaxFine(corrected_coarse, corrected_fine, 0.4)
            trueMaxCoarse = self.findTrueMaxCoarse(corrected_coarse, 0.1)

            filtered_coarse = corrected_coarse[corrected_fine <= trueMaxFine]
            filtered_fine = corrected_fine[corrected_fine <= trueMaxFine]

            filtered_fine = filtered_fine[filtered_coarse <= trueMaxCoarse]
            filtered_coarse = filtered_coarse[filtered_coarse <= trueMaxCoarse]

            numberOfCodes = ((trueMaxCoarse - 1) * trueMaxFine) + max(filtered_fine[filtered_coarse == trueMaxCoarse])
            LSB = 4000 / numberOfCodes

            tdc_codes = (filtered_coarse * (trueMaxFine)) + filtered_fine
            hist_codes = np.bincount(tdc_codes)
            averageHitsPerCode = np.mean(hist_codes[hist_codes != 0])
            possible_TDC_codes = list(range(min(tdc_codes), max(tdc_codes)))
            DNL = ((hist_codes/averageHitsPerCode)) * LSB

            DNL_cumulative = np.cumsum(DNL)

            textstr = '\n'.join((
                r'LSB=%.2f' % (LSB,),
                r'#Codes=%.2f' % (numberOfCodes,),
                r'Avg#PerCode=%.2f' % (averageHitsPerCode,)))

            ax.step(DNL_cumulative, list(range(len(hist_codes))))

            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
                    verticalalignment='top')

    def tdcHist(self, filename, basePath, formatNum, TDCNum, figureNum=1):

        _logger.info("Generating histogram")

        with h5py.File(filename, "r") as h:
            ds = h[basePath]

            plt.figure(figureNum)
            title_string = "DNL for TDC# " + str(TDCNum)
            plt.title(title_string + "\n" + basePath, fontsize=10)
            ax = plt.subplot(1, 1, 1)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))

            corrected_coarse = self.post_processing(ds, "Coarse", formatNum, tdcNum=TDCNum) # Apply post processing on Coarse
            corrected_coarse = corrected_coarse.astype('int64')

            corrected_fine = self.post_processing(ds, "Fine", formatNum, tdcNum=TDCNum)
            corrected_fine = corrected_fine.astype('int64')

            trueMaxFine = self.findTrueMaxFine(corrected_coarse, corrected_fine, 0.4)

            trueMaxCoarse = self.findTrueMaxCoarse(corrected_coarse, 0.1)

            filtered_coarse = corrected_coarse[corrected_fine <= trueMaxFine]
            filtered_fine = corrected_fine[corrected_fine <= trueMaxFine]

            filtered_fine = filtered_fine[filtered_coarse <= trueMaxCoarse]
            filtered_coarse = filtered_coarse[filtered_coarse <= trueMaxCoarse]

            tdc_codes = (filtered_coarse * trueMaxFine) + filtered_fine

            hist_codes = np.bincount(tdc_codes)
            averageHitsPerCode = np.mean(hist_codes[hist_codes != 0])

            ax.bar(np.arange(len(hist_codes)), hist_codes, align='center')

            plt.axhline(averageHitsPerCode, label='Average number of hits')



            ax.text(0.05, 0.95, "Avg#PerCode={}\n TrueMaxFine={}".format(averageHitsPerCode, trueMaxFine), transform=ax.transAxes, fontsize=14,
                    verticalalignment='top')

    def post_processing(self, h, fieldName, formatNum, tdcNum):
        if (formatNum == 1):
            return self.post_processing_PLL_FORMAT(h, fieldName)
        elif (formatNum == 0):
            mask = np.array(h['Addr'], dtype='int64')
            return self.post_processing_TDC_0_FORMAT(h, fieldName)[mask == (tdcNum*4)]
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

    def post_processing_TDC_0_FORMAT(self, h, fieldName):
        if (fieldName == "Coarse"):
            return np.array(h[fieldName], dtype='int64')

        elif (fieldName == "Fine"):
            return (np.array(h[fieldName], dtype='int64') - 2)

    # def post_processing_PLL_FORMAT(self, h, fieldName):
    #     if (fieldName == "Coarse"):
    #         ret = (np.array(h[fieldName], dtype='int64') - np.array(h['Fine'], dtype='int64'))
    #         return h[fieldName][ret == -1]
    #
    #     else:
    #         ret = (np.array(h["Coarse"], dtype='int64') - np.array(h['Fine'], dtype='int64'))
    #         dat =np.array(h[fieldName], dtype='int64')
    #         return dat[ret == -1]

if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.DEBUG)

    BH = DNLGraph()

    BH.DNL_no_jitter_cleanup("../data_grabber/NON_CORR_TDC_mar3_ALL_20min.hdf5", "CHARTIER/ASIC0/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0", TDCNum=13, formatNum=0, figureNum=1)
    BH.tdcHist("../data_grabber/NON_CORR_TDC_mar3_ALL_20min.hdf5", "CHARTIER/ASIC0/TDC/NON_CORR/FAST_255/SLOW_250/ARRAY_0", TDCNum=13, formatNum=0, figureNum=2)
    plt.show()