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


class SPTR_Window_Experiment(BasicExperiment):
    '''
    This experiement consists of activating a single SPAD for a non-correlated test

    We start by setting the HOLDOFF, RECHARGE and COMP parameters:
    HOLDOFF :: How long the SPAD stays off after a hit
    RECHARGE :: How long to recharge the SPAD after a hit
    COMP :: The comparator threshold for a hit

    How this experiment is run:
    - setup() is called once at the beginning
    - run() is then called multiple times for each combination of parameters given
    - cleanup() is called at the end. This step usually resets the ASIC

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

        self.board = Board()

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''
        self.board.mux_laser_polarity.select_input(MUX.NON_INVERTED) # 0 original, 1 inverted
        self.board.mux_coarse_delay.select_input(MUX.DELAYED_LASER) # DELAYED_LASER or MONOSTABLE

        self.board.laser_threshold.set_voltage(-0.10)

        self.board.b.LMK04610.gpio_set(0, "RESET", True)
        self.board.b.LMK04610.gpio_set(0, "RESET", False)
        self.board.b.LMK04610.gpio_set(0, "RESET", True)

        #PLL2_LD_WNDW_SIZE(0,0)
        #PLL2_LD_WNDW_SIZE_INITIAL(0,0)
        #PLL2_DLD_EN(0,1)
        #self.board.b.LMK04610.OUTCH34_LDO_BYP_MODE(0,0)
        #self.board.b.LMK04610.OUTCH34_DIV_CLKEN(0,1)
        #self.board.b.LMK04610.OUTCH34_DIV(0, 10)


        self.board.b.LMK04610.CLKIN0_EN(0,1)
        self.board.b.LMK04610.CLKIN0_SE_MODE(0,0)
        self.board.b.LMK04610.SW_REFINSEL(0, 0x4)
        self.board.b.LMK04610.PLL2EN(0,0)

        self.board.b.LMK04610.PLL2_BYP_OSC(0,1)
        self.board.b.LMK04610.PLL2_GLOBAL_BYP(0,1)

        self.board.b.LMK04610.OUTCH1_DIV_CLKEN(0,1)
        self.board.b.LMK04610.OUTCH34_DIV_CLKEN(0,1)

        self.board.b.LMK04610.OUTCH1_LDO_BYP_MODE(0,1) # 1 is bypass
        self.board.b.LMK04610.OUTCH34_LDO_BYP_MODE(0,1)

        self.board.b.LMK04610.OUTCH1_DIV(0, 80)
        self.board.b.LMK04610.OUTCH34_DIV(0, 80)

        input("Check output now")
        self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
        self.board.mux_trigger_external.select_input(MUX.PCB_INPUT) # 0 SMA, 1 trig tdc

        self.board.mux_window_laser.select_input(MUX.LASER_INPUT)
        self.board.mux_window_external.select_input(MUX.PCB_INPUT)
        self.board.asic_head_0.reset()

        time.sleep(1)

        '''Disable all external trigger. We want the SPADs to be the source of trigger'''
        self.board.asic_head_0.disable_all_ext_trigger()

        '''Set window driven mode'''
        self.board.asic_head_0.set_trigger_type(0x10)
        self.board.b.ICYSHSR1.TRIGGER_WINDOW_DRIVEN_THRESHOLD(0,1,0)
        # Set Window length
        self.board.asic_head_0.set_window_size(45)

        self.board.b.ICYSHSR1.TDC_GATING_MODE(0, 1, 0)
        self.board.asic_head_0.window_is_stop()


        '''Activate the TDC we are interrested in'''                                                     
        self.board.asic_head_0.disable_all_tdc_but(0, [2])                                 
        '''Activate the corresponding SPAD to the TDC'''                                                 
        self.board.asic_head_0.disable_all_quench_but(0, [2*4]) 


    def run(self, fast_freq, slow_freq, array, window_delay, target_spad, rch, holdoff):
        '''
        Run the experiment with the given arguments as parameters. This step is blocking and stops when the data has
        bean writen.
        :param fast_freq: Frequency of the fast oscillator (typ 255)
        :param slow_freq: Frequency of the slow oscillator (typ 250)
        :param array: Array to use (0 or 1)
        :param tdc_addr: Address of the TDC to activate, the corresponding SPAD will be activated
        :return: None
        '''


        ''' Set PLL frequencies '''
        self.board.slow_oscillator_head_0.set_frequency(slow_freq)
        self.board.fast_oscillator_head_0.set_frequency(fast_freq)

        self.board.asic_head_0.mux_select(array, 0)

        '''Set RECHARCHE current '''
        CE_T_RCH = rch #uA
        '''Set HOLDOFF current'''
        CE_T_HOLDOFF = holdoff #uA
        '''Set comparator threshold'''
        CE_V_COMP = 3.0 #V

        self.board.recharge_current.set_current(CE_T_RCH)
        self.board.holdoff_current.set_current(CE_T_HOLDOFF)
        self.board.comparator_threshold.set_voltage((CE_V_COMP/3.3) * 5)

        ''' Enable the PLL that acts as the time reference of all TDCs'''
        self.board.b.ICYSHSR1.PLL_ENABLE(0, 1, 0)

        self.board.window_delay_head_0.set_delay_code(int(window_delay))

        input("please set HV")

        '''Generate the path name to write in the HDF5'''
        path = genPathName_TDC(boardName="CHARTIER",
                               ASICNum=2,
                               matrixNum=array,
                               TDCsActive=[target_spad],
                               controlSource="PLL",
                               fastVal=fast_freq,
                               slowVal=slow_freq,
                               testType="CORR",
                               triggerType="SPAD")

        groupName = path + "/RCH_" + str(rch) + "/HOLDOFF_" + str(holdoff) + "/DELAY_" + str(window_delay)
        datasetPath = groupName + "/RAW"

        time.sleep(2)
        '''Start writing the receiving data to the file
           This function is blocking'''
        self.board.b.DMA.start_data_acquisition_HDF(self.filename, groupName, datasetPath, self.countLimit,
                                                    maxEmptyTimeout=-1,
                                                    type=1, compression=0)
        time.sleep(1)



    def cleanup(self):
        '''
        This is where you do all your cleanup. Close resources you want to free up, set back some settings to normal
        operation.
        :return:
        '''
        input("please disable hv")
        self.board.asic_head_0.reset()

if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner
    from utility.loggingSetup import loggingSetup
    import argparse
    import ast

    loggingSetup("SPTR_Window_Experiment", level=logging.DEBUG)

    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("fast_freq", help="Frequency of the fast pll")
    parser.add_argument("slow_freq", help="Frequency of the slow pll")
    parser.add_argument("array", help="Array to use on the chip (0-1)")
    parser.add_argument("window_delay", help="window_delay")
    parser.add_argument("target_spad", help="SPAD address to keep active")
    parser.add_argument("rch", help="recharge current to use (uA)")
    parser.add_argument("holdoff", help="holdoff current to use (uA)")
    parser.add_argument("-f", help="Filename of HDF5 file")
    parser.add_argument("-d", help="Folder destination of HDF5 file")
    parser.add_argument("-c", type=int, help="Data count limit")
    args = parser.parse_args()

    fast_freq = ast.literal_eval(args.fast_freq)
    slow_freq = ast.literal_eval(args.slow_freq)
    array = ast.literal_eval(args.array)
    window_delay = ast.literal_eval(args.window_delay)
    target_spad = ast.literal_eval(args.target_spad)
    rch = ast.literal_eval(args.rch)
    holdoff = ast.literal_eval(args.holdoff)


    _logger.info("fast_freq set to :" + str(fast_freq))
    _logger.info("slow_freq set to :" + str(slow_freq))
    _logger.info("array set to :" + str(array))
    _logger.info("window_delay set to :" + str(window_delay))
    _logger.info("target_spad set to :" + str(target_spad))
    _logger.info("rch set to :" + str(rch))
    _logger.info("holdoff set to :" + str(holdoff))

    # Set destination data filename
    if args.f:
        filename = args.f
    else:
        filename = "SPTR_WINDOW_TEST-" + time.strftime("%Y%m%d-%H%M%S") + ".hdf5"

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

    # Instanciate the experiment
    experiment = SPTR_Window_Experiment(filename=filename,
                                         countLimit=countLimit,
                                         timeLimit=-1)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    runner = ExperimentRunner(experiment=experiment,
                              variables={'fast_freq': fast_freq,
                                         'slow_freq': slow_freq,
                                         'array': array,
                                         'window_delay': window_delay,
                                         'target_spad': target_spad,
                                         'rch': rch,
                                         'holdoff': holdoff})

    # run and stop it. Ctrl-C can stop it prematurely.
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()
        exit()

    runner.stop()
