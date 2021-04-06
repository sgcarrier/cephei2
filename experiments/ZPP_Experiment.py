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


class ZPP_Experiment(BasicExperiment):
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

        self.basePath = "CHARTIER/ASIC0/ZPP"
        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''

        self.board.asic_head_0.frame_type_normal()

        # self.board.trigger_oscillator.set_frequency(20)  # div by 2 later
        # self.board.trigger_divider.set_divider(500, Divider.MUX_NOT_CORR)
        # self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        # self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
        # self.board.trigger_delay_head_0.set_delay_code(0)
        self.board.asic_head_0.reset()

        time.sleep(1)

        self.board.asic_head_0.disable_all_tdc()
        self.board.asic_head_0.disable_all_quench()
        self.board.asic_head_0.disable_all_ext_trigger()
        self.board.asic_head_0.configure_zpp_mode(0, 400, 200, 200)

    def run(self, array, pixel, readout, width, spacing):

        # Set PLL frequencies
        # Could be interesting to see if enabling the PLL has an impact on DCR
        # self.board.slow_oscillator_head_0.set_frequency(slow_freq)
        # self.board.fast_oscillator_head_0.set_frequency(fast_freq)
        # self.board.b.ICYSHSR1.PLL_ENABLE(0, 1, 0)

        self.board.asic_head_0.disable_all_quench_but(array, [pixel])
        self.board.asic_head_0.configure_zpp_mode(array, readout, width, spacing)


        path = "{0}/M{1}/PIXEL{2}/readout{3}/width{4}/spacing{5}".format(self.basePath, array, pixel, readout, width, spacing)
        acqID = random.randint(0, 65535)

        self.board.b.DMA.set_meta_data(self.filename, path, acqID, 4)
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
        self.board.asic_head_0.reset()

if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner
    from utility.loggingSetup import loggingSetup
    import logging

    loggingSetup("ZPP_Experiment", level=logging.DEBUG)

    # Instanciate the experiment
    filename = "ZPP-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"
    experiment = ZPP_Experiment(filename=filename,
                                countLimit=5000, timeLimit=300)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'array': 0, 'pixel': 0, 'readout': 400, 'width': 50, 'spacing': 50})

    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()
