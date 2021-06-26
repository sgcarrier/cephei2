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

""" Experiment for finding out the actual window size

    The experiment follows these steps:
    - Setup the chip in CT counting mode
    - ...
"""


class TDC_NON_CORR_DUAL_Experiment(BasicExperiment):
    '''
    This is an example of an experiment. The execution goes as follows:

    setup() (once)
    run() (multiple iterations with the variables you specify)
    cleanup (once)

    In this example, we open a hdf5 file and write to it. The variables in run() are only for illustration purposes
    and serve no role.

    Follow along in the logs and see how the experiement is doing.
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

        # Custom parameters for the example, had what you want here

        self.basePath = "/M0/TDC/NON_CORR"
        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''

        # Frames are type short
        self.board.asic_head_0.frame_type_normal()

        self.board.trigger_oscillator.set_frequency(20)  # div by 2 later
        self.board.trigger_divider.set_divider(500, Divider.MUX_NOT_CORR)
        self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
        self.board.trigger_delay_head_0.set_delay_code(0)
        self.board.asic_head_0.reset()

        time.sleep(1)

        #self.board.asic_head_0.disable_all_tdc()
        self.board.asic_head_0.disable_all_quench()
        #self.board.asic_head_0.disable_all_ext_trigger()

    def run(self, fast_freq, slow_freq, array, tdc1_addr, tdc2_addr):

        # Set PLL frequencies
        self.board.slow_oscillator_head_0.set_frequency(slow_freq)
        self.board.fast_oscillator_head_0.set_frequency(fast_freq)

        self.board.asic_head_0.disable_all_tdc_but(array, [int(tdc1_addr), int(tdc2_addr)])
        self.board.asic_head_0.disable_all_ext_trigger_but(array, [int(tdc1_addr), int(tdc2_addr)])

        self.board.b.ICYSHSR1.PLL_ENABLE(0, 1, 0)

        self.board.asic_head_0.set_trigger_type(1)
        self.board.b.ICYSHSR1.TRIGGER_EVENT_DRIVEN_COLUMN_THRESHOLD(0, 1, 0)

        path = genPathName_TDC(boardName="CHARTIER",
                               ASICNum=0,
                               matrixNum=array,
                               TDCsActive=[int(tdc1_addr), int(tdc2_addr)],
                               controlSource="PLL",
                               fastVal=fast_freq,
                               slowVal=slow_freq,
                               testType="NON_CORR",
                               triggerType="EXT")

        groupName = path
        datasetPath = path + "/RAW"

        # This line is blocking
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

    loggingSetup("TDC_NON_CORR_DUAL_Experiment", level=logging.DEBUG)

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("fast_freq", help="Frequency of the fast pll")
    parser.add_argument("slow_freq", help="Frequency of the slow pll")
    parser.add_argument("array", help="Array to use on the chip (0-1)")
    parser.add_argument("tdc1_addr", help="First TDC address to keep active")
    parser.add_argument("tdc2_addr", help="Second TDC address to keep active")
    parser.add_argument("-f", help="Filename of HDF5 file")
    parser.add_argument("-d", help="Folder destination of HDF5 file")
    parser.add_argument("-c", type=int, help="Data count limit")
    args = parser.parse_args()

    fast_freq = ast.literal_eval(args.fast_freq)
    slow_freq = ast.literal_eval(args.slow_freq)
    array = ast.literal_eval(args.array)
    tdc1_addr = ast.literal_eval(args.tdc1_addr)
    tdc2_addr = ast.literal_eval(args.tdc2_addr)

    _logger.info("fast_freq set to :" + str(fast_freq))
    _logger.info("slow_freq set to :" + str(slow_freq))
    _logger.info("array set to :" + str(array))
    _logger.info("tdc1_addr set to :" + str(tdc1_addr))
    _logger.info("tdc2_addr set to :" + str(tdc2_addr))

    # Set destination data filename
    if args.f:
        filename = args.f
    else:
        filename = "TDC_NON_CORR_DUAL-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"

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
    experiment = TDC_NON_CORR_DUAL_Experiment(filename=filename,
                                         countLimit=countLimit,
                                         timeLimit=-1)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'fast_freq': fast_freq, 'slow_freq': slow_freq, 'array': array, 'tdc1_addr': tdc1_addr, 'tdc2_addr': tdc2_addr})

    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()
