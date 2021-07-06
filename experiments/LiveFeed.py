#!/usr/bin/python3

import logging
import time
import random

from functions.helper_functions import Board
from functions.helper_functions import Divider
from functions.helper_functions import MUX


_logger = logging.getLogger(__name__)

""" Simple script to just output to the network what is passing in the DMA"""

board = Board()

try:
    board.b.DMA.start_data_acquisition(0)
except KeyboardInterrupt:
    board.b.DMA.stop_data_acquisition()
    _logger.info("Stopping live feed")
    exit()