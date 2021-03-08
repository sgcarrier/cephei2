from utility.BasicExperiment import BasicExperiment
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

temp_dtype = np.dtype({'names': ['col1', 'col2'], 'formats': ['i4', 'i4']})


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


        # for field in self.fields:
        #     if (self.basePath + "/" + field) not in self.h:
        #         self.h.create_dataset(self.basePath + '/' + field, (0,), maxshape=(None,), dtype=temp_dtype)
        self.h.create_dataset(self.basePath, (0,), maxshape=(None,), dtype=temp_dtype)


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

        #for field in self.fields:
        col1 = np.random.random_integers(0, 10, L)
        col2 = np.array([0,1,2,3,4,5,6,7,8,9])

        to_write = np.array(np.dstack((col1,col2)), dtype=temp_dtype)

        path = "/VAR1_{0}/VAR2_{1}".format(first_variable,second_variable)
        self.h[self.basePath].resize((self.h[self.basePath].shape[0] + L), axis=0)
        self.h[self.basePath][-L:] = to_write

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



if __name__ == '__main__':
    from utility.ExperimentRunner import ExperimentRunner

    logging.basicConfig(level=logging.DEBUG)


    # Instanciate the example experiment
    experiment = FakeExperiment(filename="../output/test_compound.hdf5",
                                         countLimit=50000)

    # Assign the experiment to the runner and tell the variables you have and if you want to iterate
    # in this case, first_variable doesn't change, and second_variable starts at 6000, ends at 3000 by -500 steps
    runner = ExperimentRunner(experiment=experiment,
                              variables={'first_variable': 15000, 'second_variable':(6000,3000,-500)})

    #run and stop it. Ctrl-C can stop it prematurely.
    runner.start()
    runner.stop()