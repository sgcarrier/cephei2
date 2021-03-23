import numpy as np
import h5py

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
        print("shit")
        newBasePath = "ADDR_{}".format(tdcNum)
        return np.array(h[newBasePath][fieldName], dtype='int64')

def post_processing_PLL_FORMAT(h, fieldName):
    """
    Post-Processing for the PLL frames. They are 20 bits long.
    """
    if (fieldName == "Coarse"):
        ret = (np.array(h[fieldName], dtype='int64') - (np.array(h['Fine'], dtype='int64') + 1))
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
    trueMaxCoarse = findTrueMaxCoarseWThreshold(coarse_data, threshold=0.1)

    hist_fine = np.bincount(fine_data[coarse_data <= trueMaxCoarse])
    for f in range(int(max(fine_data)/2), max(fine_data)):
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
    for c in range(1, max(coarse_data)):
        if hist_coarse[c] < (np.mean(hist_coarse)*threshold):
            decimal = hist_coarse[c-1]/np.mean(hist_coarse[1:c-2])
            return c-2+decimal

    return max(coarse_data)

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
