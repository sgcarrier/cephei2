"""
The Experiment_planner module. This module helps create experimental setup for characterizing. Instanciate the
BasicExperiment class and run experiments with the Experiment Runner
"""

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ['CorrelatedExperiment', 'ExperimentRunner', 'NonCorrelatedExperiment', 'BasicExperiment']

