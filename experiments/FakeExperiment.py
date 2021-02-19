from experiments.BasicExperiment import BasicExperiment
import h5py
import numpy as np
import logging
import time

_logger = logging.getLogger(__name__)

""" Experiment for testing and example purposes

    This example illustrate the basic structure you should follow:
    - Inherit from 'BasicExperiment' abstract class
    - Have a setup, run and cleanup functions
    - run() can have any number of arguments as you wish
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
        self.basePath = "Base/Test/Path"
        self.fields = ['Fine', 'Coarse', 'Mid']

    def setup(self):
        '''
        The setup is executed once before all the calls to run() with different iterations.
        This is where you assign setting that will not change during your experiment
        '''
        self.h = h5py.File(self.filename, "a", libver='latest')
        self.h.swmr_mode = True

        for field in self.fields:
            if (self.basePath + "/" + field) not in self.h:
                self.h.create_dataset(self.basePath + '/' + field, (0,), maxshape=(None,))


    def run(self, first_variable, second_variable):
        '''
        This is the main running function. This where you setup your experiments with specific variables for your
        acquisition. This function MUST be blocking because you are acquiring data and writing that data to an open
        file.
        :param first_variable:  The first custom variable you need
        :param second_variable: The second
        '''
        L = 10

        print("This run will use the following setup: ")
        print("Firsts variable is : " + str(first_variable))
        print("Seconds variable is : " + str(second_variable))

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
