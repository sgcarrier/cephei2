#!/usr/bin/python3

from utility.BasicExperiment import BasicExperiment
import logging
import time
import random

from functions.helper_functions import Board
from functions.helper_functions import Divider
from functions.helper_functions import MUX
from functions.helper_functions_asic import ConstantsASIC

from utility.ExperimentRunner import genPathName_TDC

_logger = logging.getLogger(__name__)

""" Experiment getting the specs of the Time-bin post-processing functionality
"""


class TimeBin_window_NON_CORR_Experiment(BasicExperiment):
    '''
    This is an example of an experiment. The execution goes as follows:

    setup() (once)
    run() (multiple iterations with the variables you specify)
    cleanup (once)

    In this example, we open a hdf5 file and write to it. The variables in run() are only for illustration purposes
    and serve no role.

    Follow along in the logs and see how the experiement is doing.
    '''

    def __init__(self, filename, countLimit=-1, timeLimit=-1):
        '''

        :param filename: Filename you will write to.
        :param countLimit: Limit of datapoints to acquire per run
        '''
        super().__init__()
        self.filename = filename
        self.countLimit = countLimit
        self.timeLimit = timeLimit

        # Custom parameters for the example, had what you want here

        self.basePath = "/M0/QKD/NON_CORR"
        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''

        self.board.trigger_oscillator.set_frequency(20)  # div by 2 later
        self.board.trigger_divider.set_divider(154, Divider.MUX_NOT_CORR)
        self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
        self.board.trigger_delay_head_0.set_delay_code(0)

        self.board.window_oscillator.set_frequency(20)
        self.board.window_divider.set_divider(500, Divider.MUX_NOT_CORR)
        self.board.mux_window_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_window_external.select_input(MUX.PCB_INPUT)
        self.board.window_delay_head_0.set_delay_code(400)

        self.board.asic_head_0.reset()

        time.sleep(1)

        # self.board.asic_head_0.disable_all_quench()
        self.board.asic_head_0.disable_all_tdc_but(0, [0])
        self.board.asic_head_0.disable_all_ext_trigger_but(0, [0])

    def run(self, fast_freq, slow_freq, delay, window_length):
        # Set PLL Frequencies and enable
        self.board.slow_oscillator_head_0.set_frequency(slow_freq)
        self.board.fast_oscillator_head_0.set_frequency(fast_freq)
        self.board.b.ICYSHSR1.PLL_ENABLE(0, 1, 0)

        # Set trigger delay
        # self.board.trigger_delay_head_0.set_delay_code(int(delay))

        # Set Window length
        self.board.asic_head_0.set_window_size(window_length)

        # Set timebins and other QKD registers
        # timeBins = [0, (window_length // 3), 2*(window_length // 3), window_length]
        self.board.asic_head_0.confgure_QKD_mode(0, [50, 100, 150, 200], threshold=1)

        self.board.b.ICYSHSR1.TIME_CONVERSION_CLOCK_PERIOD_0(0, 4000, 0)
        # self.board.asic_head_0.set_individual_spad_access(1)
        #self.board.asic_head_0.mux_select(0, ConstantsASIC.SEL_QKD_TIME_BIN)

        currPost = self.board.b.ICYSHSR1.POST_PROCESSING_SELECT(0, 0)
        _logger.info("Post processing set to : " + str(currPost))

        # self.board.asic_head_0.set_trigger_type(0x10)
        # self.board.b.ICYSHSR1.READOUT_MODE(0, 1, 0)
        #self.board.b.ICYSHSR1.TDC_GATING_MODE(0, 1, 0)
        # self.board.b.ICYSHSR1.TRIGGER_WINDOW_DRIVEN_THRESHOLD(0, 0, 0)
        #self.board.asic_head_0.window_is_stop()

        # self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_0(0, 50, 0)
        # self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_0_1(0, 100, 0)
        # self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_1_2(0, 150, 0)
        # self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_2(0, 200, 0)

        # self.board.b.ICYSHSR1.SERIAL_READOUT_TYPE(0,1,0)


        path = genPathName_TDC(boardName="CHARTIER",
                               ASICNum=0,
                               matrixNum=0,
                               TDCsActive=[0],
                               controlSource="PLL",
                               fastVal=fast_freq,
                               slowVal=slow_freq,
                               testType="NON_CORR",
                               triggerType="EXT")

        path += "/DELAY_{0}/WINDOW_LEN_{1}/".format(delay, window_length)
        groupName = path
        datasetPath = path + "/RAW"

        time.sleep(2)
        # This line is blocking
        self.board.b.DMA.start_data_acquisition_HDF(self.filename, groupName, datasetPath, self.countLimit,
                                                    maxEmptyTimeout=-1,
                                                    type=10, compression=0)
        time.sleep(1)

    def cleanup(self):
        '''
        This is where you do all your cleanup. Close resources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        self.board.asic_head_0.reset_TDC_mux()
        self.board.asic_head_0.frame_type_normal()
        self.board.asic_head_0.reset()


if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner
    from utility.loggingSetup import loggingSetup
    import argparse
    import ast

    loggingSetup("WINDOW_NON_CORR_Experiment", level=logging.DEBUG)

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("fast_freq", help="Frequency of the fast pll")
    parser.add_argument("slow_freq", help="Frequency of the slow pll")
    parser.add_argument("array", help="Array to use on the chip (0-1)")
    parser.add_argument("delay", help="Delay in PS of the trigger ")
    parser.add_argument("window_length", help="Length of window in code")
    parser.add_argument("-f", help="Filename of HDF5 file")
    parser.add_argument("-d", help="Folder destination of HDF5 file")
    parser.add_argument("-c", type=int, help="Data count limit")
    args = parser.parse_args()

    fast_freq = ast.literal_eval(args.fast_freq)
    slow_freq = ast.literal_eval(args.slow_freq)
    array = ast.literal_eval(args.array)
    delay = ast.literal_eval(args.delay)
    window_length = ast.literal_eval(args.window_length)

    _logger.info("fast_freq set to :" + str(fast_freq))
    _logger.info("slow_freq set to :" + str(slow_freq))
    _logger.info("array set to :" + str(array))
    _logger.info("delay set to :" + str(delay))
    _logger.info("window_length set to :" + str(window_length))

    # Set destination data filename
    if args.f:
        filename = args.f
    else:
        filename = "WINDOW_NON_CORR-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"

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
    experiment = TimeBin_window_NON_CORR_Experiment(filename=filename,
                                            countLimit=countLimit,
                                            timeLimit=-1)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'fast_freq': fast_freq,
                                         'slow_freq': slow_freq,
                                         'delay': delay,
                                         'window_length': window_length,
                                         'array': array})

    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()
