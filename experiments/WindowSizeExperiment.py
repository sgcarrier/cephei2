#!/usr/bin/python3

from utility.BasicExperiment import BasicExperiment
import logging
import time
import random
from tqdm import tqdm
import pickle
import numpy as np




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


class Window_Size_Experiment(BasicExperiment):
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

        self.basePath = "/MO/TDC/WINDOW"
        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''

        # Frames are type short
        self.board.asic_head_0.frame_type_normal()

        # Setup the board
        self.board.pll.set_frequencies(312.5, 312.5, 5000)
        self.board.window_divider.set_divider(2, Divider.MUX_CORR)
        self.board.trigger_divider.set_divider(2, Divider.MUX_CORR)
        self.board.mux_window_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_window_external.select_input(MUX.PCB_INPUT)
        self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
        self.board.window_delay_head_0.set_delay_code(0)        # Min delay
        self.board.trigger_delay_head_0.set_delay_code(511)     # Max delay
        self.board.asic_head_0.reset()
        self.board.asic_head_0.configure_ct_counting_mode(0, 10000)

        time.sleep(1)
        self.board.b.GEN_GPIO.gpio_set("MUX_COMM_SELECT", False)
        self.board.b.GEN_GPIO.gpio_set("EN_COMM_COUNTER", False)

        self.board.asic_head_0.disable_all_tdc()
        self.board.asic_head_0.disable_all_quench()
        #self.board.asic_head_0.disable_all_ext_trigger()

        self.pbar = tqdm(total=self.countLimit)


    def run(self, window_length, delay, array):
        self.board.asic_head_0.enable_all_ext_trigger()
        self.board.asic_head_0.set_window_size(window_length)
        self.board.asic_head_0.configure_ct_counting_mode(array, 10000)
        self.board.asic_head_0.set_window_size(window_length)

        #self.board.b.ICYSHSR1.PLL_ENABLE(0, 1, 0)

        #self.board.b.ICYSHSR1.SERIAL_READOUT_TYPE(0, 1, 0)
        #self.board.asic_head_0.set_trigger_type(1)
        #self.board.b.ICYSHSR1.TRIGGER_EVENT_DRIVEN_COLUMN_THRESHOLD(0, 1, 0)

        if delay < 0:
            self.board.window_delay_head_0.set_delay_code(-delay)
            self.board.trigger_delay_head_0.set_delay_code(0)
        else:
            self.board.window_delay_head_0.set_delay_code(0)
            self.board.trigger_delay_head_0.set_delay_code(delay)

        # TODO: Change format
        path = genPathName_TDC( boardName="CHARTIER",
                                ASICNum=0,
                                matrixNum=array,
                                TDCsActive="ALL",
                                controlSource="PLL",
                                fastVal=window_length,
                                slowVal=delay,
                                testType="WINDOW_LENGTH",
                                triggerType="EXT")

        groupName = path
        datasetPath = path + "/RAW"

        #path = "{0}/FAST_{1}/SLOW_{2}/ARRAY_{3}".format(self.basePath, fast_freq, slow_freq, array)
        acqID = random.randint(0, 65535)

        #self.board.b.DMA.set_meta_data(self.filename, path, acqID, 0)
        time.sleep(1)
        # This line is blocking
        #self.board.b.DMA.start_data_acquisition(acqID, self.countLimit, self.timeLimit, maxEmptyTimeout=100)
        self.board.b.DMA.start_data_acquisition_HDF(self.filename, groupName, datasetPath, self.countLimit, maxEmptyTimeout=-1,
                                                    type=0, compression=0)
        time.sleep(1)



    def cleanup(self):
        '''
        This is where you do all your cleanup. Close resources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        self.board.asic_head_0.reset()
        self.pbar.close()


    def progressBar(self):
        if self.countLimit != -1:
            self.pbar = tqdm(total=self.countLimit)
            self.pbar.close()

if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner
    from utility.loggingSetup import loggingSetup
    import argparse
    import ast

    loggingSetup("Window_Size_Experiment", level=logging.DEBUG)

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("array", help="Array to use on the chip (0-1)")
    parser.add_argument("winlen", help="Length of the window (0-255)")
    parser.add_argument("steps", help="Steps")
    parser.add_argument("-f", help="Filename of HDF5 file")
    parser.add_argument("-d", help="Folder destination of HDF5 file")
    parser.add_argument("-c", type=int, help="Data count limit")
    args = parser.parse_args()

    array = ast.literal_eval(args.array)
    winlen = ast.literal_eval(args.winlen)
    steps = ast.literal_eval(args.steps)

    _logger.info("array set to :" + str(array))

    # Set destination data filename
    if args.f:
        filename = args.f
    else:
        filename = "Window_Size_Experiment-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"

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

    experiment = Window_Size_Experiment(filename=filename,
                                                countLimit=countLimit,
                                                timeLimit=-1)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'window_length': winlen, 'delay': (-1024, 1024, steps), 'array': array})


    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()