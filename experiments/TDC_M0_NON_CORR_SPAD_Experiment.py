#!/usr/bin/python3

from utility.BasicExperiment import BasicExperiment
import logging
import time
import random

from functions.helper_functions import Board
from functions.helper_functions import Divider
from functions.helper_functions import MUX

from utility.ExperimentRunner import genPathName_TDC

_logger = logging.getLogger(__name__)


class TDC_NON_CORR_SPAD_Experiment(BasicExperiment):
    '''
    This experiement consists of activating a single SPAD for a non-correlated test

    We start by setting the HOLDOFF, RECHARGE and COMP parameters:
    HOLDOFF :: How long the SPAD stays off after a hit
    RECHARGE :: How long to recharge the SPAD after a hit
    COMP :: The comparator threshold for a hit

    How this experiment is run:
    - setup() is called once at the beginning
    - run() is then called multiple times for each combination of parameters given
    - cleanup() is called at the end. This step usually resets the ASIC

    '''

    def __init__(self, filename, countLimit, timeLimit):
        '''

        :param filename: Filename you will write to.
        :param countLimit: Limit of datapoints to acquire per run
        '''
        super().__init__()
        self.filename = filename
        self.countLimit = countLimit
        self.timeLimit = timeLimit

        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''

        self.board.asic_head_0.reset()

        time.sleep(1)

        '''Disable all external trigger. We want the SPADs to be the source of trigger'''
        self.board.asic_head_0.disable_all_ext_trigger()


    def run(self, fast_freq, slow_freq, array, tdc_addr):
        '''
        Run the experiment with the given arguments as parameters. This step is blocking and stops when the data has
        bean writen.
        :param fast_freq: Frequency of the fast oscillator (typ 255)
        :param slow_freq: Frequency of the slow oscillator (typ 250)
        :param array: Array to use (0 or 1)
        :param tdc_addr: Address of the TDC to activate, the corresponding SPAD will be activated
        :return: None
        '''


        ''' Set PLL frequencies '''
        self.board.slow_oscillator_head_0.set_frequency(slow_freq)
        self.board.fast_oscillator_head_0.set_frequency(fast_freq)

        '''Set RECHARCHE current '''
        CE_T_RCH =  11 #uA (10 ns)
        '''Set HOLDOFF current'''
        CE_T_HOLDOFF = 1 #uA (240 ns)
        '''Set comparator threshold'''
        CE_V_COMP = 3 #V

        self.board.recharge_current.set_current(CE_T_RCH)
        self.board.holdoff_current.set_current(CE_T_HOLDOFF)
        self.board.comparator_threshold.set_voltage((CE_V_COMP/3.3) * 5)

        '''Activate the TDC we are interrested in'''
        self.board.asic_head_0.disable_all_tdc_but(array, [6])
        '''Activate the corresponding SPAD to the TDC'''
        self.board.asic_head_0.disable_all_quench_but(array, [24,25])

        ''' Enable the PLL that acts as the time reference of all TDCs'''
        self.board.b.ICYSHSR1.PLL_ENABLE(0, 1, 0)

        '''Generate the path name to write in the HDF5'''
        path = genPathName_TDC(boardName="CHARTIER",
                               ASICNum=0,
                               matrixNum=array,
                               TDCsActive=[6],
                               controlSource="PLL",
                               fastVal=fast_freq,
                               slowVal=slow_freq,
                               testType="NON_CORR",
                               triggerType="SPAD")

        groupName = path
        datasetPath = path + "/RAW"

        time.sleep(2)
        '''Start writing the receiving data to the file
           This function is blocking'''
        self.board.b.DMA.start_data_acquisition_HDF(self.filename, groupName, datasetPath, self.countLimit,
                                                    maxEmptyTimeout=-1,
                                                    type=1, compression=0)
        time.sleep(1)



    def cleanup(self):
        '''
        This is where you do all your cleanup. Close resources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        self.board.asic_head_0.reset()

if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner
    from utility.loggingSetup import loggingSetup
    import argparse
    import ast

    loggingSetup("TDC_NON_CORR_SPAD_Experiment", level=logging.DEBUG)

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("fast_freq", help="Frequency of the fast pll")
    parser.add_argument("slow_freq", help="Frequency of the slow pll")
    parser.add_argument("array", help="Array to use on the chip (0-1)")
    parser.add_argument("tdc_addr", help="TDC address to keep active")
    parser.add_argument("-f", help="Filename of HDF5 file")
    parser.add_argument("-d", help="Folder destination of HDF5 file")
    parser.add_argument("-c", type=int, help="Data count limit")
    args = parser.parse_args()

    fast_freq = ast.literal_eval(args.fast_freq)
    slow_freq = ast.literal_eval(args.slow_freq)
    array = ast.literal_eval(args.array)
    tdc_addr = ast.literal_eval(args.tdc_addr)

    _logger.info("fast_freq set to :" + str(fast_freq))
    _logger.info("slow_freq set to :" + str(slow_freq))
    _logger.info("array set to :" + str(array))
    _logger.info("tdc_addr set to :" + str(tdc_addr))

    # Set destination data filename
    if args.f:
        filename = args.f
    else:
        filename = "TDC_NON_CORR-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"

    if args.d:
        if (args.d[-1] == '/'):
            filename = args.d + filename
        else:
            filename = args.d + "/" + filename

    if args.c:
        countLimit = args.c
    else:
        _logger.warning("No countlimit set, setting to 10000 by default")
        countLimit = 10000

    # Instanciate the experiment
    experiment = TDC_NON_CORR_SPAD_Experiment(filename=filename,
                                         countLimit=countLimit,
                                         timeLimit=-1)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'fast_freq': fast_freq, 'slow_freq': slow_freq, 'array': array, 'tdc_addr': tdc_addr})

    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()
