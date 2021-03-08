import itertools
import numpy as np
import logging

_logger = logging.getLogger(__name__)


class ExperimentRunner:
    """
    Runs experiments given a set of variables to iterate over. It's basically a fancy wrappers to avoid writting a
    bunch of for loops yourself.
    """

    def __init__(self, experiment, variables, visualizer=None, skipSetup=False):
        """
        Construct a new ExperimentRunner object

        :param experiment: The experiment to use. Expects a BasicExperiment type object
        :param variables: Dictionnary of variables that will be passed to the experiement. If a value is an integer,
        the value wont change, but if given a tuple with length 3 (start, stop, step), that variable will iterate.
        """
        self.__experiment = experiment
        self.__variables = variables
        self.__visualizer = visualizer
        _logger.info("Done Initializing the Experiment runner")

    def start(self):
        """
        Start the experiment. Launches the setup() and run() of the experiment. Attaches the visualizer if there is one
        :return: Nothing
        """

        _logger.info("Starting Setup")
        self.__experiment.setup()
        _logger.info("Done Setup")

        currentVars = self.__variables
        allCombinations = []
        varsThatChange = []
        for key, val in currentVars.items():
            if isinstance(val, int) or isinstance(val, float):
                currentVars[key] = val
            elif isinstance(val, tuple):
                currentVars[key] = val[0]
                if len(val) == 3:
                    allCombinations.append(np.arange(val[0], val[1], val[2]))
                    varsThatChange.append(key)
                else:
                    _logger.error("Error in val formating. Tuples must be onf size 3: (start, stop, step)")
            else:
                _logger.error("Error in val formating. Expecting int or tuple")
                return

        if self.__visualizer and self.__experiment.filename:
            _logger.info("Starting Visualizer")
            try:
                self.__visualizer.open(self.__experiment.filename)
                self.__experiment.subscribe(self.__visualizer)
                self.__visualizer.setBasePath("Base/Test/Path")
                self.__visualizer.start()
            except TypeError:
                _logger.error("Error when connecting Visualizer to experiment")
        else:
            _logger.info("No Visualizer or file specified, skipping...")

        _logger.info("Starting Experiment")

        listOfAllCombinations = itertools.product(*allCombinations)

        for iterNum, varValues in enumerate(listOfAllCombinations, start=1):
            for i in range(len(varsThatChange)):
                currentVars[varsThatChange[i]] = varValues[i]
            _logger.info("Starting iteration {}/? with variables {}".format(iterNum, currentVars))
            #_logger.info("Starting iteration" + str(iterNum) + "/" + str(len(listOfAllCombinations)) + " with variables: " + str(currentVars))
            self.__experiment.run(**currentVars)

        _logger.info("Done Experiment")


    def stop(self):
        """
        Stop the experiment. Runs the cleanup() of the experiment
        :return:
        """
        _logger.info("Starting Cleanup")
        self.__experiment.cleanup()
        _logger.info("Done Cleanup")




def genPathName(testSection, ):
    testSectionOptions = ['PLL', 'QKD', 'CT', 'GENERIC']
    triggerSourceOptions = ['EXT', 'SPAD_ARRAY', 'EXT_SPAD']
    matrixOptions = ['M0', 'M1']
    postProcessingOptions = [0, 1, 2, 3, 4, 5]
    TDCoptions = ['SINGLE_TDC', 'MULTI_TDC']
    TDCServiceOptions = ['EXT_DAC', 'PLL']
    pass
