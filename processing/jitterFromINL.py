import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import h5py
import pickle
from processing.visuPostProcessing import findMatchingTDCEventsFast
from ICYSHSR1_transfer_function_ideal import TransferFunctions
from transferFunctionChip import TransferFunction
import matplotlib.mlab as mlab
from scipy.stats import norm
from matplotlib.ticker import MaxNLocator
from collections import Counter
from scipy.optimize import curve_fit
from scipy.interpolate import UnivariateSpline


"""
    Defining gaussian for curve fitting
"""
def gaussian(x, mean, amplitude, standard_deviation):
    return amplitude * np.exp(- (x - mean)**2 / (2*standard_deviation ** 2))

# Datasets
#filename = "C:\\Users\\labm1507\\Documents\\DATA\\NON_CORR_TEST_ALL-20210325-192849.hdf5"
#path = "CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL"

#----TEST de base 2 TDC ASIC 0-----
#filename = "C:\\Users\\labm1507\\Documents\\DATA\\NON_CORR_TEST_0_4-20210331-201117.hdf5"
#path = "CHARTIER/ASIC0/TDC/M0/2_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_0_1"

#----TEST all ASIC 0 envent driven non skip-----
#filename = "C:\\Users\\labm1507\\Documents\\DATA\\NON_CORR_TEST_ALL-20210414-212030.hdf5"
#path = "CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW"

"""
    Constant setup for different test case
    
    SAVED_DATA: 0 = generate timestamps from new datasets and generate pickle file of calculated timestamps
                1 = use previously generated pickle file for timestamps (data.p must be present in root folder)
    ADDR_PIX_1: Address of first TDC for comparison (value range 0 to 48)
    ADDR_PIX_2: Address of second TDC for comparison (value range 0 to 48)
    PROCESSING: 0 = Use ideal transfer function to calculate timestamps
                1 = Use in chip algorithm to calculate timestamps
                2 = Use both ideal transfer function and in chip processing for comparison
    FILTER:     Value of the threshold for filtering 
"""
SAVED_DATA = 0
ADDR_PIX_1 = 0
ADDR_PIX_2 = 1
PROCESSING = 0
FILTER = 0.00

"""
Main star here
"""

normalisedAddr1 = ADDR_PIX_1 * 4
normalisedAddr2 = ADDR_PIX_2 * 4

if 0 > SAVED_DATA > 1:
    print("Saved data config", SAVED_DATA, "invalid (must be 0 or 1)")
    exit()
if 0 > ADDR_PIX_1 > 48 or 0 > ADDR_PIX_2 > 48:
    print("Chosen address out of range (must be between 0 and 48")
    exit()
if 0 > PROCESSING > 2:
    print("Processing type", PROCESSING, "is invalid (must be 0 or 1)")
    exit()


if SAVED_DATA == 0:
    filename = "C:\\Users\\labm1507\\Documents\\DATA\\NON_CORR_TEST_ALL-20210414-212030.hdf5"
    path = "CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW"

    if PROCESSING == 0:
        idealTF1 = TransferFunctions(filename=filename,
                                     basePath=path,
                                     pixel_id=normalisedAddr1,
                                     filter_lower_than=FILTER)
        idealTF2 = TransferFunctions(filename=filename,
                                     basePath=path,
                                     pixel_id=normalisedAddr2,
                                     filter_lower_than=FILTER)
        plt.figure()
        plt.plot(idealTF1.get_ideal())
        plt.plot(idealTF2.get_ideal())

        plt.figure()
        plt.plot(idealTF1.get_ideal())
        plt.plot(idealTF2.get_ideal())

    with h5py.File(filename, "r") as h:

        # Get the data pointer

        ds = h[path]
        d1, d2 = findMatchingTDCEventsFast(normalisedAddr1, normalisedAddr2, ds)

        print("value post treatement tdc1 =", len(d1))
        print("value post treatement tdc2 =", len(d2))

        if PROCESSING == 0 or 2:
            jitterIdeal = []
        if PROCESSING == 1 or 2:
            jitterChip = []

        for coarse_1, fine_1, coarse_2, fine_2, globalCounter_1, globalCounter_2 in zip(d1['Coarse'], d1['Fine'], d2['Coarse'], d2['Fine'], d1['Global'], d2['Global']):
            if PROCESSING == 0 or 2:
                try:
                    if coarse_1 != 0 and coarse_2 != 0:
                        timestampIdeal1 = (idealTF1.code_to_timestamp(coarse_1 - 1, fine_1))
                        timestampIdeal2 = (idealTF2.code_to_timestamp(coarse_2 - 1, fine_2))
                        diffCounter = globalCounter_1*4000-globalCounter_2*4000
                        print(diffCounter)
                        jitterIdeal.append(round(timestampIdeal1 - timestampIdeal2) - diffCounter)

                        print("-------------------")
                        print("coarse_1 =", coarse_1)
                        print("fine_1 =", fine_1)
                        print("TS_1 =", timestampIdeal1)
                        print("coarse_2 =", coarse_2)
                        print("fine_2 =", fine_2)
                        print("TS_2 =", timestampIdeal2)
                        print("-------------------")
                except:
                    print("-------------------")
                    print("coarse_1 =", coarse_1)
                    print("fine_1 =", fine_1)
                    print("coarse_2 =", coarse_2)
                    print("fine_2 =", fine_2)
                    print("-------------------")
                    pass
                pickle.dump(jitterIdeal, open("TSIdeal.p", "wb"))
            if PROCESSING == 1 or 2:
                try:
                    timestampChip1 = TransferFunction.evaluate(fine_1, coarse_1, normalisedAddr1)
                    timestampChip2 = TransferFunction.evaluate(fine_2, coarse_2, normalisedAddr2)
                    jitterChip.append(round(timestampChip1 - timestampChip2))

                    print("-------------------")
                    print("coarse_1 =", coarse_1)
                    print("fine_1 =", fine_1)
                    print("TS_1 =", timestampChip1)
                    print("coarse_2 =", coarse_2)
                    print("fine_2 =", fine_2)
                    print("TS_2 =", timestampChip2)
                    print("-------------------")
                except:
                    print("------ERROR-------")
                    print("coarse_1 =", coarse_1)
                    print("fine_1 =", fine_1)
                    print("coarse_2 =", coarse_2)
                    print("fine_2 =", fine_2)
                    print("-------------------")
                    pass
elif SAVED_DATA == 1:
    jitterIdeal = pickle.load(open("TSIdeal.p", "rb"))

meanTemp = np.mean(jitterIdeal)
stdTemp = np.std(jitterIdeal)

discardedData = [x for x in jitterIdeal if (x < meanTemp - 6 * stdTemp)]
discardedData.extend([x for x in jitterIdeal if (x > meanTemp + 6 * stdTemp)])

percentDiscard = (len(discardedData) / len(jitterIdeal)) * 100

#print("percentDiscard=", "%.4f" % percentDiscard, "%")

jitterFinal = [x for x in jitterIdeal if (x > meanTemp - 6 * stdTemp)]
jitterFinal = [x for x in jitterFinal if (x < meanTemp + 6 * stdTemp)]

meanTemp = np.mean(jitterFinal)

jitterFinal = [round(x - meanTemp) for x in jitterFinal]

jitterMin = np.amin(jitterFinal)
jitterMax = np.amax(jitterFinal)
jitterMedian = np.median(jitterFinal)
jitterMean = np.mean(jitterFinal)
jitterStd = np.std(jitterFinal)
jitterFWHM = jitterStd*2.355

#print("Min =", jitterMin)
#print("Max =", jitterMax)
#print("Median =", jitterMedian)
#print("Mean =", jitterMean)
#print("STD =", jitterStd)
#print("FWHM =", jitterFWHM)

bin_range = [min(jitterFinal)-0.5]

for i in range(max(jitterFinal)-min(jitterFinal)):
    bin_range.append(i+min(jitterFinal)+0.5)

#print("freq table=", bin_range)
plt.figure()
#--Plot--
#Histogram
ax = plt.subplot(111)
n, bins, _ = ax.hist(jitterFinal, bins=bin_range)

#Curve Fitting
bin_centers = bins[:-1] + np.diff(bins) / 2
popt, pcov = curve_fit(gaussian, bin_centers, n, p0=[1., 0., 1.])
x_interval_for_fit = np.linspace(bins[0], bins[-1], 10000)
fitGaussian = gaussian(x_interval_for_fit, *popt)
plt.plot(x_interval_for_fit, fitGaussian, label='fit')

print("fitGaussian:", pcov)

#FWHM
spline = UnivariateSpline(x_interval_for_fit, fitGaussian-np.max(fitGaussian)/2, s=0)
r1, r2 = spline.roots() # find the roots
ax.axvspan(r1, r2, edgecolor='black', facecolor='None', alpha=0.5, label='FWHM')

#Title
ax.set_title("Timestamp Difference TDC " + str(round(normalisedAddr1 / 4)) + " and TDC " + str(round(normalisedAddr2 / 4)), fontsize=18, fontweight="bold")

#Axis Title
ax.set_xlabel("Timestamp", fontsize=15)
ax.set_ylabel("Frequency", fontsize=15)

#Stats

jitterFWHM = r2-r1
jitterStd = jitterFWHM/2.355

textStr = '\n'.join((
    r'Discarded Data=%.4f' % (percentDiscard,),
    r'Min=%.0f' % (jitterMin,),
    r'Max=%.0f' % (jitterMax,),
    r'Mean=%.0f' % (jitterMean,),
    r'Median=%.0f' % (jitterMedian,),
    r'STD=%.2f' % (jitterStd,),
    r'FWHM=%.2f' % (jitterFWHM,)))

ax.text(0.05, 0.95, textStr, transform=ax.transAxes, fontsize=14,
        verticalalignment='top')
#Show plot
plt.legend()
plt.show()