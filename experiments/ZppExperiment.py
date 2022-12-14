#!/usr/bin/python3

from utility.BasicExperiment import BasicExperiment
import h5py
import numpy as np
import logging
import time

from functions.helper_functions import Board
from functions.helper_functions import Divider
from functions.helper_functions import MUX


_logger = logging.getLogger(__name__)



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
        self.basePath = "ZPP"
        self.fields = ['Fine', 'Coarse', 'Mid']
        self.board = Board()
        self.pixels_enabled = [0]

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
        self.board.asic_head_0.reset()
        self.board.asic_head_0.disable_all_quench_but(0, self.pixels_enabled)
        self.board.asic_head_0.configure_zpp_mode(0, 3000, 55, 35)

    def run(self, width, spacing):
        # String du path
        expPath = self.basePath + '/width_' + str(width) + '/spacing_' + str(spacing)
        metadata = {'width': width,
                    'spacing': spacing}
        # Format de la trame attendue

        time.sleep(1)

    def cleanup(self):
        '''
        This is where you do all your cleanup. Close ressources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        self.h.close()
