#!/usr/bin/python3
from utility.BasicExperiment import BasicExperiment
import numpy as np
import logging
import time

from functions.agilent_scope_functions import delayLineAgilent
from functions.helper_functions import Board
from functions.helper_functions import Divider
from functions.helper_functions import MUX

_logger = logging.getLogger(__name__)

delay_line_type = np.dtype({'names': ['delay_obj', 'delay_code_bit', 'ftune', 'hits', 'mean', 'std_dev', 'start_temp', 'end_temp'],
                            'formats': ['i4', 'i4', 'f4', 'i4', 'f4', 'f4', 'f4', 'f4']})


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
        VISA_ADDRESS = 'TCPIP0::192.168.0.100::inst0::INSTR'
        dataFolder = "C:/Users/Administrator/Documents/SimonCarrier/DATA"
        setupFile = "C:/Users/Administrator/Documents/SimonCarrier/SETUP/delay_line_setup.set"
        self.agilent = delayLineAgilent(VISA_ADDRESS, dataFolder, setupFile)

        self.board.trigger_oscillator.set_frequency(20)  # div by 2 later
        self.board.trigger_divider.set_divider(50, Divider.MUX_NOT_CORR)
        self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
        self.board.trigger_delay_head_0.set_delay_code(0)

        self.datafile_prefix = "delay_line_charac-" + time.strftime("%Y%m%d-%H%M%S")
        self.dataTotal = np.array([], dtype=delay_line_type)

        currTemp = 0
        prevTemp = 50
        while(abs(prevTemp - currTemp) >= 1):
            _logger.info("Currently checking the temperature stability. This might take a while")
            prevTemp = self.board.temp_probe.get_temp()
            _logger.info("Current temperature = " + str(prevTemp))

            time.sleep(120)

            currTemp =  self.board.temp_probe.get_temp()
            _logger.info("Current temperature = " + str(currTemp))

    def run(self, delay_ps):
        '''
        This is the main running function. This where you setup your experiments with specific variables for your
        acquisition. This function MUST be blocking because you are acquiring data and writing that data to an open
        file.
        :param first_variable:  The first custom variable you need
        :param second_variable: The second
        '''
        time.sleep(1)


        actual_delay, delay_code, ftune_volt = self.board.trigger_delay_head_0.delay_to_bit_code_and_ftune(delay_ps)

        self.board.trigger_delay_head_0.set_fine_tune(ftune_volt)
        self.board.trigger_delay_head_0.set_delay_code(delay_code)

        time.sleep(3)

        start_temp = self.board.temp_probe.get_temp()

        datafile_name = self.datafile_prefix + "_delay_ps_" + str(delay_ps)
        n_hits, mean, std_dev = self.agilent.start_acq(self.countLimit, datafile_name)

        end_temp = self.board.temp_probe.get_temp()

        data = np.array([(actual_delay, delay_code, ftune_volt, n_hits, mean, std_dev, start_temp, end_temp)], dtype=delay_line_type)
        _logger.info("Current Acquisition returned : " + str(data))

        self.dataTotal = np.append(self.dataTotal, data)

        with open(self.datafile_prefix + ".csv", "ab") as f:
            np.savetxt(f, data, delimiter=',')

        time.sleep(1)

    def cleanup(self):
        '''
        This is where you do all your cleanup. Close ressources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        # self.h.close()
        print(self.dataTotal)
        np.savetxt(self.datafile_prefix + ".csv", self.dataTotal, delimiter=",")

        self.agilent.close()


if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner
    from utility.loggingSetup import loggingSetup
    import argparse
    import ast

    loggingSetup("DelayLineExperiment", level=logging.DEBUG)

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("delay_code_bit", help="Bit to set to 1 in the 10 bit delay code (0-9)")
    parser.add_argument("ftune", help="Ftune value of the SY89296U delay line. Controlled by the DAC (0-65535)")
    parser.add_argument("-f", help="Filename of HDF5 file")
    parser.add_argument("-d", help="Folder destination of HDF5 file")
    parser.add_argument("-c", type=int, help="Data count limit")
    args = parser.parse_args()

    delay_code_bit = ast.literal_eval(args.delay_code_bit)
    ftune = ast.literal_eval(args.ftune)

    _logger.info("delay_code_bit set to :" + str(delay_code_bit))
    _logger.info("ftune set to :" + str(ftune))

    # Set destination data filename
    if args.f:
        filename = args.f
    else:
        filename = "DELAY_LINE-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"

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

    # Instanciate the example experiment
    experiment = DelayLineExperiment(filename=filename,
                                     countLimit=countLimit)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'delay_code_bit': delay_code_bit, 'ftune': ftune})

    # run and stop it. Ctrl-C can stop it prematurely.
    runner.start()
    runner.stop()