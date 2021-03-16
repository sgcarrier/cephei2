from utility.BasicExperiment import BasicExperiment
import logging
import time
import random

from functions.helper_functions import Board
from functions.helper_functions import Divider
from functions.helper_functions import MUX


_logger = logging.getLogger(__name__)

""" Experiment for finding out the actual window size

    The experiment follows these steps:
    - Setup the chip in CT counting mode
    - ...
"""


class TDC_PLL_CORR_Experiment(BasicExperiment):
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

        # Frames are type short
        self.board.asic_head_0.frame_type_short()

        #Setting external trigger
        #self.board.pll.set_frequencies(10, 10, 5000)
        self.board.pll.set_6_25mhz()
        self.board.trigger_divider.set_divider(500, Divider.MUX_CORR)
        self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
        self.board.trigger_delay_head_0.set_delay_code(0)
        self.board.asic_head_0.reset()

        time.sleep(1)

        self.board.asic_head_0.disable_all_tdc()
        self.board.asic_head_0.disable_all_quench()
        self.board.asic_head_0.disable_all_ext_trigger()

        self.board.asic_head_0.test_TDC_PLL()

    def run(self, fast_freq, slow_freq, delay):

        self.board.slow_oscillator_head_0.set_frequency(slow_freq)
        self.board.fast_oscillator_head_0.set_frequency(fast_freq)
        self.board.trigger_delay_head_0.set_delay_code(int(delay))


        #path = self.basePath + "/FAST_" + str(fast_freq) + "/SLOW_" + str(slow_freq) + "/DELAY"
        path = "{0}/FAST_{1}/SLOW_{2}/DELAY_{3}".format(self.basePath, fast_freq, slow_freq, delay)
        acqID = random.randint(0, 65535)

        self.board.b.DMA.set_meta_data(self.filename, path, acqID, 1)
        time.sleep(2)
        # This line is blocking
        self.board.b.DMA.start_data_acquisition(acqID, self.countLimit, maxEmptyTimeout=100)
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
    import logging

    loggingSetup("TDC_PLL_CORR_Experiment", level=logging.DEBUG)

    # Instanciate the experiment
    experiment = TDC_PLL_CORR_Experiment(filename="../output/example_NON_CORR_TEST.hdf5",
                                         countLimit=10000)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'fast_freq': 255, 'slow_freq': 250, 'delay':(0, 1000, 200)})

    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()
