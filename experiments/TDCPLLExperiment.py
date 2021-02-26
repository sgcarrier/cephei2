from utility.BasicExperiment import BasicExperiment
import h5py
import numpy as np
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


class TDCPLLExperiment(BasicExperiment):
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

        self.basePath = "/PLL/TDC"
        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''
        self.board.asic_head_0.disable_all_tdc()
        self.board.asic_head_0.disable_all_quench()
        self.board.asic_head_0.disable_all_ext_trigger()

    def run(self, fast_freq, slow_freq):

        self.board.slow_oscillator_head_0.set_frequency(slow_freq)
        self.board.fast_oscillator_head_0.set_frequency(fast_freq)

        path = self.basePath + "/FAST" + str(fast_freq) + "/SLOW" + str(slow_freq)
        acqID = random.randint(0, 65535)

        self.board.b.DMA.set_meta_data(path, acqID, 1)
        time.sleep(1)
        self.board.b.DMA.start_data_acquisition(acqID, self.countLimit)
        time.sleep(1)

    def cleanup(self):
        '''
        This is where you do all your cleanup. Close ressources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        pass

if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner

    logging.basicConfig(level=logging.DEBUG)

    # Instanciate the example experiment
    experiment = TDCPLLExperiment(filename="../output/example_NON_CORR_TEST.hdf5",
                                  countLimit=1000)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    # in this case, first_variable doesn't change, and second_variable starts at 6000, ends at 3000 by -500 steps
    runner = ExperimentRunner(experiment=experiment,
                              variables={'fast_freq': 252.5, 'slow_freq': 250})

    # run and stop it. Ctrl-C can stop it prematurely.
    runner.start()
    runner.stop()
