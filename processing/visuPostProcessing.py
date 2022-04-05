import numpy as np
import h5py
import pandas as pd
from scipy import stats
from tqdm import tqdm

def post_processing(h, fieldName, formatNum, tdcNum, mask=None):
    if (formatNum == 1):
        return post_processing_PLL_FORMAT(h, fieldName)
    else:
        return post_processing_RAW_FORMAT(h, fieldName, tdcNum, mask)

def post_processing_RAW_FORMAT(h, fieldName, tdcNum, mask=None):
    """
    Post-Processing for the RAW frames. They are 64 bits long.
    We are only interested in the ones with the corresponding TDC number
    Do the x4 to the TDC number because there is 1 TDC per 4 pixels
    """

    if isinstance(h, h5py.Dataset):  # This is for cases we did all TDC at the same time
        if mask is not None:
            ht = h[fieldName][mask]
            return ht[h['Addr'][mask] == (tdcNum * 4)]
        else:
            ht = h[fieldName]
            return ht[h['Addr'] == (tdcNum * 4)]
    else:  # This is for cases where we did one TDC at a time
        newBasePath = "ADDR_{}".format(tdcNum)
        return np.array(h[newBasePath][fieldName], dtype='int64')

def post_processing_RAW_FORMAT_FINE_COARSE_NO_SKIP(h, tdcNum, maxTDC):

    if isinstance(h, h5py.Dataset):  # This is for cases we did all TDC at the same time

        fine = np.array(h['Fine'])[h['Addr'] == (tdcNum * 4)]
        coarse = np.array(h['Coarse'])[h['Addr'] == (tdcNum * 4)]
        glob = np.array(h['Global'])[h['Addr'] == (tdcNum * 4)]

        mask = np.zeros((len(glob),))
        td = 0
        for i in range(5000):
            if td == h['Addr'][i]:
                mask[i] = 1
                td += 4
            else:
                mask[i-td:i]= [0]*((td)//4)
                td = 0

            if td >= maxTDC*4:
                td = 0

        bmask = mask != 0
        fine_ns = fine[bmask]
        coarse_ns = coarse[bmask]

        return fine_ns, coarse_ns






    # else:  # This is for cases where we did one TDC at a time
    #     newBasePath = "ADDR_{}".format(tdcNum)
    #     return np.array(h[newBasePath][fieldName], dtype='int64')

def post_processing_PLL_FORMAT(h, fieldName):
    """
    Post-Processing for the PLL frames. They are 20 bits long.
    """
    if (fieldName == "Coarse"):
        ret = (np.array(h[fieldName], dtype='int64') - (np.array(h['Fine'], dtype='int64'))) + 1
        return ret

    elif (fieldName == "Fine"):
        dat = np.array(h[fieldName], dtype='int64')
        return dat


def findTrueMaxFineWThreshold(coarse_data, fine_data, threshold):
    """
    Find the true number of fine using threshold method.
    This checks the count in every valid coarse and assigns a fractional number to the max coarse.
    This is because the last fines are often just caused by jitter.
    """
    trueMaxCoarse = findTrueMaxCoarseWThreshold(coarse_data, threshold=0.01)
    fineWGoodCoarse = fine_data[coarse_data <= trueMaxCoarse]

    hist_fine = np.bincount(fineWGoodCoarse)
    for f in range(10, max(fineWGoodCoarse)):
        if hist_fine[f] < (max(hist_fine)*threshold):
            return f-1

    return max(fine_data)

def findTrueMaxCoarseWThreshold(coarse_data, threshold):
    """
    Find the true number of coarse using the threshold method.
    This is used to avoid glitched high coarses from skewing the results
    Recommended threshold = 0.1
    """
    hist_coarse = np.bincount(coarse_data)
    for c in range(2, max(coarse_data)):
        if hist_coarse[c] < (np.mean(hist_coarse)*threshold):
            return c-1
    return max(coarse_data)

def findTrueMaxCoarseDecimal(coarse_data, threshold):
    """
    Find the true number of coarse using the threshold method.
    This is used to avoid glitched high coarses from skewing the results
    Recommended threshold = 0.1
    """
    hist_coarse = np.bincount(coarse_data)
    for c in range(3, max(coarse_data)+1):
        if hist_coarse[c] < (np.mean(hist_coarse)*threshold):
            decimal = hist_coarse[c-1]/np.mean(hist_coarse[1:c-2])
            return c-2+decimal

    decimal = hist_coarse[max(coarse_data)]/np.mean(hist_coarse[1:max(coarse_data)-1])

    return max(coarse_data)-1+decimal

def findCoarseTiming(coarse_data):
    """
    Find the true number of fine using threshold method.
    This checks the count in every valid coarse and assigns a fractional number to the max coarse.
    This is because the last fines are often just caused by jitter.
    """
    coarseTiming = 4000/coarse_data
    return coarseTiming

def findResolution(coarse_data, fine_data):
    """
    Find the true number of fine using threshold method.
    This checks the count in every valid coarse and assigns a fractional number to the max coarse.
    This is because the last fines are often just caused by jitter.
    """
    resolution = round(4000/(coarse_data*fine_data))
    return resolution


def findMatchingTDCEvents(tdc1Num, tdc2Num, data):
    '''
    Finds the events with the same Global Counter (the same event) and returns the Coarse and Fine columns for both
    TDCs. They are ordered in matching pairs.
    :param tdc1Num: Number of the TDC # 1 to use
    :param tdc2Num: Number of the TDC # 2 to use
    :param data: Raw data, dont filter out the column names
    :return: the coarse,fine columns of all matched events for TDC#1 and TDC#2
    '''
    '''Extract the data concerning the 2 TDCs we are comparing'''
    TDC1Data = data[(data["Addr"] == tdc1Num)]
    TDC2Data = data[(data["Addr"] == tdc2Num)]
    # Set columns Coarse and Fine
    data_type = np.dtype({'names': ['Coarse', 'Fine'], 'formats': ['u4', 'u4']})

    '''Initialize an array as big as we think it will be'''
    data1 = np.zeros(max([len(TDC1Data), len(TDC2Data)]), dtype=data_type)
    data2 = np.zeros(max([len(TDC1Data), len(TDC2Data)]), dtype=data_type)


    idx = 0
    for i in (range(len(TDC1Data))):
        '''Find global counter matches from data1 in data2. The indexes don't match, but should be fairly close [-5,5]'''
        for j in range(-5, 6, 1):

            '''To not go out of bounds [0, len]'''
            if ((i+j) < 0) or ((i+j) >= len(TDC2Data['Global'])):
                continue

            '''The [-1,1] gap is for valid rare cases that the skew caused the global counters to be different by 1'''
            if (abs(TDC1Data['Global'][i] - TDC2Data['Global'][i+j]) <= 1) :

                data1[idx] = TDC1Data[['Coarse', 'Fine']][i]
                data2[idx] = TDC2Data[['Coarse', 'Fine']][i+j]
                idx += 1
                '''We found the match, no need to look at other neighbors, break'''
                break

    '''Remove the trailing zeros'''
    data1 = np.resize(data1, idx)
    data2 = np.resize(data2, idx)

    return data1, data2

def findMatchingTDCEventsFast(tdc1Num, tdc2Num, data):
    '''
    Finds the events with the same Global Counter (the same event) and returns the Coarse and Fine columns for both
    TDCs. They are ordered in matching pairs.
    :param tdc1Num: Number of the TDC # 1 to use
    :param tdc2Num: Number of the TDC # 2 to use
    :param data: Raw data, dont filter out the column names
    :return: the coarse,fine columns of all matched events for TDC#1 and TDC#2
    '''
    TDC1Data = data[(data["Addr"] == tdc1Num)]
    TDC2Data = data[(data["Addr"] == tdc2Num)]

    # Set columns Coarse and Fine
    data_type = np.dtype({'names': ['Coarse', 'Fine', 'Global'], 'formats': ['u4', 'u4', 'u4']})

    data1 = np.zeros(max([len(TDC1Data), len(TDC2Data)]), dtype=data_type)
    data2 = np.zeros(max([len(TDC1Data), len(TDC2Data)]), dtype=data_type)

    print("len pre traitement TDC1 = ", len(TDC1Data))

    if len(TDC1Data) > len(TDC2Data):
        TDCtemp = TDC2Data
        TDC2Data = TDC1Data
        TDC1Data = TDCtemp

    shift = len(TDC1Data) - len(TDC2Data)
    step = 0
    idx = 0
    for i in (range(len(TDC1Data))):
        if (i + step) >= len(TDC2Data['Global']):
            continue

        globalDiff = TDC1Data['Global'][i] - TDC2Data['Global'][i + step]
        if (1 >= globalDiff) or (globalDiff >= -1):
            data1[idx] = TDC1Data[['Coarse', 'Fine', 'Global']][i]
            data2[idx] = TDC2Data[['Coarse', 'Fine', 'Global']][i]
        else:
            step = step+shift
            data1[idx] = TDC1Data[['Coarse', 'Fine', 'Global']][i]
            data2[idx] = TDC2Data[['Coarse', 'Fine', 'Global']][i+step]
        idx += 1


    data1 = np.resize(data1, idx)
    data2 = np.resize(data2, idx)
    #print(len(data1))
    return data1, data2




def processDiffTimestamp(data, maxFine, maxCoarse):
    global_data = data["Global"]
    timestampDiff = np.zeros((len(global_data) - 1,), dtype="int64")
    for i in range(len(global_data) - 1):
        if (global_data[i + 1] - global_data[i]) >= 0:
            timeDiff = self.calcTimestamp(global_data[i+1], data["Fine"][i+1], data["Coarse"][i+1], maxFine, maxCoarse) - self.calcTimestamp(global_data[i], data["Fine"][i], data["Coarse"][i], maxFine, maxCoarse)
            timestampDiff[i] = timeDiff
        else:  # in the case that the global counter overflows
            timeDiff = self.calcTimestamp(global_data[i+1]+0x1FFFFF, data["Fine"][i+1], data["Coarse"][i+1], maxFine, maxCoarse) - self.calcTimestamp(global_data[i], data["Fine"][i], data["Coarse"][i], maxFine, maxCoarse)
            timestampDiff[i] = timeDiff
    return np.bincount(timestampDiff-np.min(timestampDiff))

def processRelTimestamp(data, maxFine):
    fine_data = data["Fine"]
    timestampRel = np.zeros((len(fine_data),), dtype="int64")
    for i in range(len(timestampRel) - 1):
        timestampRel[i] = self.calcTimestampCode( data["Fine"][i], data["Coarse"][i], maxFine)
    return np.bincount(timestampRel)

def processHistogram(data, addr, field):

    if field not in data.dtype.fields:
        return pd.DataFrame({'x': [], 'y': []})

    filteredData = data[data["Addr"] == addr]
    filteredData = filteredData[field]

    hist = np.bincount(filteredData)
    lengthData = len(hist)

    return pd.DataFrame({'x': np.arange(lengthData), 'y': hist})


def processHistogramAll(data, field):

    if field not in data.dtype.fields:
        return pd.DataFrame({'x': [], 'y': []})

    #filteredData = data[data["Addr"] == addr]
    filteredData = data[field]

    hist = np.bincount(filteredData)
    lengthData = len(hist)

    return pd.DataFrame({'x': np.arange(lengthData), 'y': hist})

def processCountRate(data, addr):

    if data.size <= 1:
        return 0

    single_tdc = False
    if (addr is not None) and (addr != -1):
        data = data[data["Addr"] == addr]
        single_tdc = True

    if data.size <= 1:
        return 0

    if ("Energy" in data.dtype.fields) and ("Global" in data.dtype.fields) and single_tdc:
        count_plot = np.zeros((len(data) - 1,), dtype="uint64")

        for i in range(len(data) - 1):
            if (np.int64(data['Global'][i + 1] - data['Global'][i])) > 0:
                # Convert from 4ns steps to KHz
                if (data['Energy'][i + 1] == 0):
                    count_plot[i] = 4 / (np.int64((data['Global'][i + 1] - data['Global'][i])) * 4) * 1000000
                else:
                    count_plot[i] = (data['Energy'][i + 1] / 4) / (
                                (np.int64(data['Global'][i + 1] - data['Global'][i])) * 4) * 1000000
            else:  # in the case that the global counter overflows
                time_diff = (0x1FFFFF - data['Global'][i]) + data['Global'][i + 1]
                # Convert from 4ns steps to KHz
                if (data['Energy'][i + 1] == 0):
                    count_plot[i] = 4 / (time_diff * 4) * 1000000
                else:
                    count_plot[i] = (data['Energy'][i + 1] / 4) / (time_diff * 4) * 1000000

        return np.mean(count_plot)

    elif ("Window" in data.dtype.fields) and single_tdc:
        windowSteps = data["Window"][-1] - data["Window"][0]

        if windowSteps < 0:
            windowSteps = (data["Window"][-1]+0x1FFFFF) - data["Window"][0]

        return (len(data) / windowSteps)

    elif ("Energy" in data.dtype.fields) and ("Global" in data.dtype.fields) and not single_tdc:
        energy_data = np.zeros((len(data) - 1,))
        global_data = np.zeros((len(data) - 1,))
        count_plot = np.zeros((len(data) - 1,))

        i = 0
        energy_data[i] = data["Energy"][0]
        global_data[i] = data["Global"][0]
        for j in range(1, len(data)):
            if global_data[i] == global_data[j]:
                energy_data[i] += energy_data[j]
            else:
                i += 1
                global_data[i] = global_data[j]
                energy_data[i] = energy_data[j]

        energy_data = energy_data[:i]
        global_data = global_data[:i]
        count_plot = np.zeros((len(global_data) - 1,))

        for i in range(len(data) - 1):
            if (global_data[i + 1] - global_data[i]) > 0:
                # Convert from 4ns steps to KHz
                if (energy_data[i + 1] == 0):
                    count_plot[i] = 4 / ((global_data[i + 1] - global_data[i]) * 4) * 1000000
                else:
                    count_plot[i] = (energy_data[i + 1] ) / (
                            (global_data[i + 1] - global_data[i]) * 4) * 1000000
            else:  # in the case that the global counter overflows
                time_diff = (0x1FFFFF - global_data[i]) + global_data[i + 1]
                # Convert from 4ns steps to KHz
                if (energy_data[i + 1] == 0):
                    count_plot[i] = 4 / (time_diff * 4) * 1000000
                else:
                    count_plot[i] = (energy_data[i + 1] ) / (time_diff * 4) * 1000000

        return np.mean(count_plot)


    return 0



def calcPeak(data, addr, peak_acceptance_factor):
    reduced_data  = data[data['Addr'] == addr]
    if "Timestamp" in reduced_data.dtype.fields:
        mode = stats.mode(reduced_data['Timestamp'])
        hist = np.bincount(reduced_data['Timestamp'])
        hist = hist[hist != 0]
        avg_count = np.mean(hist)
        if mode[1] > (peak_acceptance_factor*avg_count):
            return int(mode[0][0])
        else:
            return -1
    else:
        return -1

def processSPADImage(data):
    if (data.size == 0):
        return np.zeros((8,8)),np.zeros((8,8)),np.zeros((8,8)),np.zeros((8,8)),np.zeros((8,8))
    maxAddr = np.max(data["Addr"])
    arraySize = int(np.ceil(np.sqrt(maxAddr))**2)
    side = int(np.sqrt(arraySize))
    image = np.zeros((side,side))
    bin1_image = np.zeros((side, side))
    bin2_image = np.zeros((side, side))
    bin3_image = np.zeros((side, side))
    dca_image = np.zeros((side, side))
    counts = np.zeros((arraySize,))
    bin1_counts = np.zeros((arraySize,))
    bin2_counts = np.zeros((arraySize,))
    bin3_counts = np.zeros((arraySize,))
    dca_counts = np.zeros((arraySize,))

    for i in range(arraySize):
        counts[i] = len(data[data["Addr"] == i])
        if "Bin" in data.dtype.fields:
            bin1_counts[i] = len(data[(data["Addr"] == i) & (data["Bin"] == 1)])
            bin2_counts[i] = len(data[(data["Addr"] == i) & (data["Bin"] == 2)])
            bin3_counts[i] = len(data[(data["Addr"] == i) & (data["Bin"] == 3)])
        if "DCA" in data.dtype.fields:
            dca_counts[i] = len(data[(data["Addr"] == i) & (data["DCA"] == 1)])

    for i in range(side * side):
        tdc = i // 4
        sub = i % 4

        x_pos = (2 * tdc) % side + (sub % 2)
        if (sub < 2):
            y_pos = ((tdc) // (side//2)) * 2
        else:
            y_pos = ((tdc) // (side//2)) * 2 +1

        image[x_pos][y_pos] = counts[i]
        bin1_image[x_pos][y_pos] = bin1_counts[i]
        bin2_image[x_pos][y_pos] = bin2_counts[i]
        bin3_image[x_pos][y_pos] = bin3_counts[i]
        dca_image[x_pos][y_pos] = dca_counts[i]


    return image, bin1_image, bin2_image, bin3_image, dca_image



def processTotalCountRate(data):

    if ("Energy" in data.dtype.fields) and ("Global" in data.dtype.fields):
        if data["Global"].size == 0:
            return 0
        totalEnergy = np.sum(data["Energy"])

        #Count number of times global counter reset
        toAdd = 0
        for i in range(len(data["Global"])-1):
            if data["Global"][i+1] < data["Global"][i]:
                toAdd += 0x1FFFFF

        totalTime = ((data["Global"][-1]+toAdd) - data["Global"][0])

        countRate = totalEnergy / (totalTime * 4) * 1000000 # in khz

        return countRate

    else:
        return 0


def calcMaxCoarse(filename, path):
    with h5py.File(filename, 'r') as h:
        data = h[path]
        maxCoarse = findTrueMaxCoarseDecimal(data["Coarse"], threshold=0.1)

    return maxCoarse


def calcMaxFine(filename, path):
    with h5py.File(filename, 'r') as h:
        data = h[path]
        maxFine = findTrueMaxFineWThreshold(data["Coarse"], data["Fine"], threshold=0.01)

    return maxFine

