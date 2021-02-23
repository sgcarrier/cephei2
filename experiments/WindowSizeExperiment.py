from experiments.BasicExperiment import BasicExperiment
import h5py
import numpy as np
import logging
import time

from scripts.helper_functions import Board
from scripts.helper_functions import Divider
from scripts.helper_functions import MUX


_logger = logging.getLogger(__name__)

""" Experiment for finding out the actual window size

    The experiment follows these steps:
    - Setup the chip in CT counting mode
    - ...
"""


class FakeExperiment(BasicExperiment):
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
        self.h = None
        self.basePath = "WindowSize"
        self.fields = ['Fine', 'Coarse', 'Mid']
        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''
        self.h = h5py.File(self.filename, "a", libver='latest')
        self.h.swmr_mode = True

        # Prepare the HDF file
        for field in self.fields:
            if (self.basePath + "/" + field) not in self.h:
                self.h.create_dataset(self.basePath + '/' + field, (0,), maxshape=(None,))

        # Setup the board
        self.board.pll.set_frequencies(10, 10, 5000)
        self.board.window_divider.set_divider(2, Divider.MUX_CORR)
        self.board.trigger_divider.set_divider(2, Divider.MUX_CORR)
        self.board.mux_window_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_window_external.select_input(MUX.PCB_INPUT)
        self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
        self.board.window_delay_head_0.set_delay_code(0)
        self.board.trigger_delay_head_0.set_delay_code(511)     # Max delay
        self.board.asic_head_0.reset()
        self.board.asic_head_0.configure_ct_counting_mode(0, 3000)

    def run(self, window_length, delay):
        L = 10

        print("This run will use the following setup: ")
        print("Firsts variable is : " + str(window_length))
        print("Seconds variable is : " + str(delay))

        for field in self.fields:
            r = np.random.random_integers(0, 10, L)
            self.h[self.basePath + '/' + field].resize((self.h[self.basePath + '/' + field].shape[0] + L), axis=0)
            self.h[self.basePath + '/' + field][-L:] = r

        self.h.attrs['CurrSetRef'] = self.h[self.basePath].ref

        self.h.flush()

        time.sleep(1)

    def cleanup(self):
        '''
        This is where you do all your cleanup. Close ressources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        self.h.close()
