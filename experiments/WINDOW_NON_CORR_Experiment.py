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


class WINDOW_NON_CORR_Experiment(BasicExperiment):
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
        # self.board.asic_head_0.confgure_QKD_mode(0, timeBins, threshold=1)

        self.board.b.ICYSHSR1.TIME_CONVERSION_CLOCK_PERIOD_0(0, 4000, 0)
        # self.board.asic_head_0.set_individual_spad_access(1)
        self.board.asic_head_0.mux_select(0, 0)

        currPost = self.board.b.ICYSHSR1.POST_PROCESSING_SELECT(0, 0)
        _logger.info("Post processing set to : " + str(currPost))

        # self.board.asic_head_0.set_trigger_type(0x10)
        # self.board.b.ICYSHSR1.READOUT_MODE(0, 1, 0)
        self.board.b.ICYSHSR1.TDC_GATING_MODE(0, 1, 0)
        # self.board.b.ICYSHSR1.TRIGGER_WINDOW_DRIVEN_THRESHOLD(0, 0, 0)
        self.board.asic_head_0.window_is_stop()

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

        acqID = random.randint(0, 65535)

        self.board.b.DMA.set_meta_data(self.filename, path, acqID, 0, attributes={"PP": 0,
                                                                                  "TDC_GATING_MODE": 1,
                                                                                  "WINDOW_IS_STOP": 1})
        time.sleep(2)
        # This line is blocking
        self.board.b.DMA.start_data_acquisition(acqID, self.countLimit, self.timeLimit, maxEmptyTimeout=100)
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
    import logging

    loggingSetup("QKD_WINDOW_NON_CORR_Experiment", level=logging.DEBUG)

    # Instanciate the experiment
    filename = "WINDOW_NON_CORR_Experiment-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"
    experiment = WINDOW_NON_CORR_Experiment(filename=filename,
                                                countLimit=1000000,
                                                timeLimit=-1)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'fast_freq': (254, 257, 1),
                                         'slow_freq': 250,
                                         'delay': 0,
                                         'window_length': (5, 251, 5)})

    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()
