#!/usr/bin/python3
from utility.BasicExperiment import BasicExperiment
import h5py
import numpy as np
import logging
import time

from functions.agilent_scope_functions import delayLineAgilent
from functions.helper_functions import Board
from functions.helper_functions import Divider
from functions.helper_functions import MUX


_logger = logging.getLogger(__name__)

delay_line_type = np.dtype({'names': ['delay_code_bit', 'hits', 'mean', 'std_dev', 'start_temp', 'end_temp'], 'formats': ['i4', 'i4', 'f4', 'f4', 'f4', 'f4']})


class DelayLineExperiment(BasicExperiment):
    '''
    This is an experiment for characterizing the delay line. The execution goes as follows:

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
        self.basePath = "/BOARD_0/TRIGGER"

        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''
        VISA_ADDRESS = 'TCPIP0::10.51.92.166::inst0::INSTR'
        dataFolder = "C:/Users/Administrator/Documents/SimonCarrier/DATA"
        setupFile = "C:/Users/Administrator/Documents/SimonCarrier/SETUP/delay_line_setup.set"
        self.agilent = delayLineAgilent(VISA_ADDRESS, dataFolder, setupFile)
        self.h = h5py.File(self.filename, "a", libver='latest')
        self.h.create_dataset(self.basePath, (0,), maxshape=(None,), dtype=delay_line_type)

        self.board.trigger_oscillator.set_frequency(20)  # div by 2 later
        self.board.trigger_divider.set_divider(500, Divider.MUX_NOT_CORR)
        self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
        self.board.trigger_delay_head_0.set_delay_code(0)

        self.datafile_prefix = "delay_line_charac-" + time.strftime("%Y%m%d-%H%M%S")


    def run(self, delay_code_bit, ftune):
        '''
        This is the main running function. This where you setup your experiments with specific variables for your
        acquisition. This function MUST be blocking because you are acquiring data and writing that data to an open
        file.
        :param first_variable:  The first custom variable you need
        :param second_variable: The second
        '''

        delay_code = 1 << delay_code_bit
        self.board.trigger_delay_head_0.set_delay_code(delay_code)
        self.board.trigger_delay_head_0.set_fine_tune(ftune)

        time.sleep(3)

        start_temp = self.board.temp_probe.get_temp()

        datafile_name = self.datafile_prefix+"_delay_" + str(delay_code) + "_ftune_" + str(ftune)
        n_hits, mean, std_dev = self.agilent.start_acq(self.countLimit, datafile_name)

        end_temp = self.board.temp_probe.get_temp()

        data = np.array([(delay_code_bit, n_hits, mean, std_dev, start_temp, end_temp)], dtype=delay_line_type)

        self.h[self.basePath].resize((self.h[self.basePath].shape[0] + 1), axis=0)
        self.h[self.basePath][-1:] = data

        self.h.flush()

        time.sleep(1)

    def cleanup(self):
        '''
        This is where you do all your cleanup. Close ressources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        self.h.close()



if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner

    logging.basicConfig(level=logging.DEBUG)


    # Instanciate the example experiment
    filename = "DELAY_LINE-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"
    experiment = DelayLineExperiment(filename=filename,
                                         countLimit=1000000)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'delay_code_bit': (0, 10, 1), 'ftune': (0, 65536, 257)})

    #run and stop it. Ctrl-C can stop it prematurely.
    runner.start()
    runner.stop()