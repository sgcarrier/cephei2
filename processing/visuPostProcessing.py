import numpy as np
import h5py
from tqdm import tqdm

def post_processing(h, fieldName, formatNum, tdcNum):
    if (formatNum == 1):
        return post_processing_PLL_FORMAT(h, fieldName)
    else:
        return post_processing_RAW_FORMAT(h, fieldName, tdcNum)

def post_processing_RAW_FORMAT(h, fieldName, tdcNum):
    """
    Post-Processing for the RAW frames. They are 64 bits long.
    We are only interested in the ones with the corresponding TDC number
    Do the x4 to the TDC number because there is 1 TDC per 4 pixels
    """

    if isinstance(h, h5py.Dataset):  # This is for cases we did all TDC at the same time
        return np.array(h[fieldName])[h['Addr'] == (tdcNum * 4)]
    else:  # This is for cases where we did one TDC at a time
        newBasePath = "ADDR_{}".format(tdcNum)
        return np.array(h[newBasePath][fieldName], dtype='int64')

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
    for c in range(1, max(coarse_data)):
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
    for c in range(1, max(coarse_data)+1):
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
    for i in tqdm(range(len(TDC1Data))):
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
    for i in tqdm(range(len(TDC1Data))):
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
    print(len(data1))
    return data1, data2



