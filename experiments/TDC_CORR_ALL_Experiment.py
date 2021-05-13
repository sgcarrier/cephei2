#!/usr/bin/python3

from utility.BasicExperiment import BasicExperiment
import logging
import time
import random

from utility.ExperimentRunner import genPathName_TDC

from functions.helper_functions import Board
from functions.helper_functions import Divider
from functions.helper_functions import MUX


_logger = logging.getLogger(__name__)

""" Experiment for finding out the actual window size

    The experiment follows these steps:
    - Setup the chip in CT counting mode
    - ...
"""


class TDC_CORR_ALL_Experiment(BasicExperiment):
    '''
    This is an example of an experiment. The execution goes as follows:

    setup() (once)
    run() (multiple iterations with the variables you specify)
    cleanup (once)

    In this example, we open a hdf5 file and write to it. The variables in run() are only for illustration purposes
    and serve no role.

    Follow along in the logs and see how the experiement is doing.
    '''

    def __init__(self, filename, countLimit):
        '''

        :param filename: Filename you will write to.
        :param countLimit: Limit of datapoints to acquire per run
        '''
        super().__init__()
        self.filename = filename
        self.countLimit = countLimit

        # Custom parameters for the example, had what you want here

        self.basePath = "/PLL/TDC/CORR"
        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''

        #Setting external trigger
        #self.board.pll.set_frequencies(10, 10, 5000)
        self.board.pll.set_6_25mhz()
        self.board.trigger_divider.set_divider(500, Divider.MUX_CORR)
        self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
        self.board.trigger_delay_head_0.set_delay_code(0)
        self.board.asic_head_0.reset()

        time.sleep(1)

        self.board.asic_head_0.disable_all_quench()

    def run(self, fast_freq, slow_freq, array,  delay):

        self.board.b.ICYSHSR1.SERIAL_READOUT_TYPE(0, 0, 0)

        # Set PLL frequencies
        self.board.slow_oscillator_head_0.set_frequency(slow_freq)
        self.board.fast_oscillator_head_0.set_frequency(fast_freq)

        # Set delay
        actual_delay, delay_code, ftune_volt = self.board.trigger_delay_head_0.delay_to_bit_code_and_ftune(delay)
        self.board.trigger_delay_head_0.set_fine_tune(ftune_volt)
        self.board.trigger_delay_head_0.set_delay_code(delay_code)

        self.board.asic_head_0.enable_all_tdc()
        self.board.asic_head_0.enable_all_ext_trigger()

        self.board.b.ICYSHSR1.PLL_ENABLE(0, 1, 0)

        # self.board.b.ICYSHSR1.SERIAL_READOUT_TYPE(0, 1, 0)
        self.board.asic_head_0.set_trigger_type(1)
        self.board.b.ICYSHSR1.TRIGGER_EVENT_DRIVEN_COLUMN_THRESHOLD(0, 1, 0)

        path = genPathName_TDC(boardName="CHARTIER",
                               ASICNum=0,
                               matrixNum=array,
                               TDCsActive="ALL",
                               controlSource="PLL",
                               fastVal=fast_freq,
                               slowVal=slow_freq,
                               testType="CORR",
                               triggerType="EXT")

        groupName = path
        datasetPath = path + "/RAW"


        time.sleep(1)
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
        self.board.asic_head_0.reset_TDC_mux()
        self.board.asic_head_0.frame_type_normal()

if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner
    from utility.loggingSetup import loggingSetup
    import argparse
    import ast

    loggingSetup("TDC_CORR_ALL_Experiment", level=logging.DEBUG)

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("fast_freq", help="Frequency of the fast pll")
    parser.add_argument("slow_freq", help="Frequency of the slow pll")
    parser.add_argument("array", help="Array to use on the chip (0-1)")
    parser.add_argument("delay_ps", help="Array to use on the chip (0-1)")
    parser.add_argument("-f", help="Filename of HDF5 file")
    parser.add_argument("-d", help="Folder destination of HDF5 file")
    parser.add_argument("-c", type=int, help="Data count limit")
    args = parser.parse_args()

    fast_freq = ast.literal_eval(args.fast_freq)
    slow_freq = ast.literal_eval(args.slow_freq)
    array = ast.literal_eval(args.array)
    delay_ps = ast.literal_eval(args.delay_ps)

    _logger.info("fast_freq set to :" + str(fast_freq))
    _logger.info("slow_freq set to :" + str(slow_freq))
    _logger.info("array set to :" + str(array))
    _logger.info("delay_ps set to :" + str(delay_ps))

    # Set destination data filename
    if args.f:
        filename = args.f
    else:
        filename = "TDC_CORR_ALL-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"

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

    experiment = TDC_CORR_ALL_Experiment(filename=filename,
                                                countLimit=countLimit)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'fast_freq': fast_freq, 'slow_freq': slow_freq, 'array': array, 'delay_ps': delay_ps})

    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()
