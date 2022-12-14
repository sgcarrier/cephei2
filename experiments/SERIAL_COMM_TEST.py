#!/usr/bin/python3

from utility.BasicExperiment import BasicExperiment
import logging
import time
import random
from tqdm import tqdm





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


class SERIAL_COMM_TEST(BasicExperiment):
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
        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''

        self.board.b.GEN_GPIO.gpio_set("MUX_COMM_SELECT", True)
        self.board.b.GEN_GPIO.gpio_set("EN_COMM_COUNTER", True)

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

        self.pbar = tqdm(total=self.countLimit)

    def run(self, fast_freq, slow_freq, array):



        path = genPathName_TDC( boardName="CHARTIER",
                                ASICNum=0,
                                matrixNum=array,
                                TDCsActive="ALL",
                                controlSource="PLL",
                                fastVal=fast_freq,
                                slowVal=slow_freq,
                                testType="NON_CORR",
                                triggerType="EXT")

        groupName = path.split("/")
        groupName = "/".join(groupName[:-1])

        time.sleep(1)
        #self.board.b.GEN_GPIO.gpio_set("EN_COMM_COUNTER", True)
        # This line is blocking
        self.board.b.DMA.start_data_acquisition_HDF(self.filename, groupName, path, self.countLimit, maxEmptyTimeout=-1)
        time.sleep(1)



    def cleanup(self):
        '''
        This is where you do all your cleanup. Close resources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        self.board.asic_head_0.reset()
        self.pbar.close()
        self.board.b.GEN_GPIO.gpio_set("EN_COMM_COUNTER", False)
        self.board.b.GEN_GPIO.gpio_set("MUX_COMM_SELECT", False)


    def progressBar(self):
        if self.countLimit != -1:
            self.pbar = tqdm(total=self.countLimit)
            self.pbar.close()

if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner
    from utility.loggingSetup import loggingSetup
    import logging

    loggingSetup("SERIAL_COMM_TEST", level=logging.DEBUG)

    # Instanciate the experiment
    filename = "SERIAL_COMM_TEST-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"
    experiment = SERIAL_COMM_TEST(filename=filename,
                                                countLimit=1500000, timeLimit=-1)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'fast_freq': 255, 'slow_freq': 250, 'array': 0})


    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()
