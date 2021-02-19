from abc import ABC, abstractmethod
#from visualisation.BasicVisualizer import BasicVisualizer
"""
    Abstract class for a basic experiment. Use the setup, run, cleanup functions for arranging your experiment and
    use the ExperimentRunner to automate your test depending on the variables set with 
"""


class BasicExperiment(ABC):

    def __init__(self):
        self.subscribers = []

    @property
    def experimentVariables(self):
        try:
            return self.__experimentVariables
        except AttributeError:
            raise NotImplementedError('Subclass must have experimentVariables defined')

    @experimentVariables.setter
    def experimentVariables(self, value):
        pass

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def run(self): # This enforces the implementation of run, but doesnt limit the number of arguments you will add
        pass

    @abstractmethod
    def cleanup(self):
        pass

    def subscribe(self, obj):
        pass
        '''
        if isinstance(obj, BasicVisualizer):
            self.subscribers.append(obj)
        else:
            raise TypeError
        '''

