from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from functions.helper_functions import *



class DevkitControl():

    def __init__(self):
        self.board = None

    def connect(self, ip):
        pass
        #self.board = Board(remoteIP=ip)

    def send(self):
        pass