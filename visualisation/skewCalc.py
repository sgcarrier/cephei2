import h5py
import logging
import numpy as np
import math

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from processing.visuPostProcessing import *
from processing.ICYSHSR1_transfer_function_ideal import *
_logger = logging.getLogger(__name__)


def search_sequence_numpy(arr, seq):
    """ Find sequence in an array using NumPy only.

    Parameters
    ----------
    arr    : input 1D array
    seq    : input 1D array

    Output
    ------
    Output : 1D Array of indices in the input array that satisfy the
    matching of input sequence in the input array.
    In case of no match, an empty list is returned.
    """

    # Store sizes of input array and sequence
    Na, Nseq = arr.size, seq.size

    # Range of sequence
    r_seq = np.arange(Nseq)

    # Create a 2D array of sliding indices across the entire length of input array.
    # Match up with the input sequence & get the matching starting indices.
    M = (arr[np.arange(Na - Nseq + 1)[:, None] + r_seq] == seq).all(1)

    # Get the range of those indices as final output
    if M.any() > 0:
        return np.where(np.convolve(M, np.ones((Nseq), dtype=int)) > 0)[0]
    else:
        return []  # No match found


def skewCalc(filename, basePath, formatNum, figureNum=1, numberOfTDCs=49, title=None):
    _logger.info("Generating covariance with filtering")

    tfs = []

    for tdcNum in range(numberOfTDCs):
        tfs.append(TransferFunctions(filename=filename, basePath=basePath, pixel_id=tdcNum * 4))

    with h5py.File(filename, "r") as h:
        ds = h[basePath]

        idx = search_sequence_numpy(ds["Addr"][:100000], np.array((range(0, (numberOfTDCs * 4) - 3, 4))))

        SAMPLES = len(idx)//numberOfTDCs

        timestamps = np.zeros((numberOfTDCs, SAMPLES))
        skews = np.zeros((numberOfTDCs, ))


        for tdcNum in range(numberOfTDCs):
            coarse = post_processing(ds, "Coarse", formatNum, tdcNum=tdcNum, mask=idx)
            fine = post_processing(ds, "Fine", formatNum, tdcNum=tdcNum, mask=idx)
            timestamps[tdcNum, :] = [tfs[tdcNum].code_to_timestamp(c, f) for c, f in zip(coarse, fine)]

        timestamps_min = timestamps

        timestamps_min = np.subtract(timestamps_min, timestamps_min[0, :])

        # for s in range(SAMPLES):
        #     timestamps_min[:, s] -= np.min(timestamps_min[:,s])



        skews = np.nanmean(timestamps_min, axis=1)



        #skews_pos = skews - np.min(skews)
        skews_pos = -(skews - np.amax(skews))



    _logger.info("Done Generating covariance matrix with filtering and closed file")
