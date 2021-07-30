from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from PyQt5 import QtWidgets, uic
from pyqtgraph import PlotWidget, ColorMap
import pyqtgraph as pg

from processing.dataFormats import getFrameDtype
from processing.visuPostProcessing import processHistogram, processSPADImage
from data_grabber.multicastDataGrabber import MulticastDataGrabber
import random
from utility.QTextEditLogger import QTextEditLogger
import logging


_logger = logging.getLogger(__name__)

class DevkitView(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(DevkitView, self).__init__(*args, **kwargs)

        # Load the UI Page
        uic.loadUi('MainWindow.ui', self)

        self.dataFormat = 0
        dtype = getFrameDtype(self.dataFormat, keepRaw=False)
        self.currentLiveData_H0 = np.zeros((0,), dtype=dtype)
        self.currentLiveData_H1 = np.zeros((0,), dtype=dtype)


        self.maxSamples = 1000
        self.tdcOfInterest = 0
        self.headOfInterest = 0
        self.barGraphs = []

        self.monitorList = ['Fine', 'Coarse']
        self.graphsReady = True

        self.buildView()

        self.mdg = MulticastDataGrabber()

        self.logTextBox = None
        self.setupLogger()

    def setupLogger(self):
        self.logTextBox = QTextEditLogger(self.logTextBrowser)
        # You can format what is printed to text box
        self.logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.DEBUG)

    def connect(self):
        _logger.info("Connecting to network for viewer")
        try:
            self.mdg.connectToNetwork()
        except Exception as e:
            _logger.warning("Failed to connect to network with error: " + str(e))

    def buildView(self):

        for field in self.monitorList:
            self.barGraphs.append(pg.BarGraphItem(x=[], height=[], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title=field)
            p.addItem(self.barGraphs[-1])
            self.liveDataGraph.nextRow()

        self.clearDataButton.clicked.connect(self.clearLiveData)

        self.graphTypeSelect.addItems(["Histogram", "Timestamp"])
        self.graphTypeSelect.currentIndexChanged.connect(self.selectionChanged)

        self.maxSamplesSelect.setMaximum(10 ** 8)
        self.maxSamplesSelect.setValue(self.maxSamples)
        self.maxSamplesSelect.valueChanged.connect(self.newMaxSamples)

        self.tdcNumberSelect.setMaximum(192)
        self.tdcNumberSelect.setValue(self.tdcOfInterest)
        self.tdcNumberSelect.valueChanged.connect(self.newtdcOfInterest)

        self.headNumberSelect.addItems(["H0", "H1"])
        self.headNumberSelect.currentIndexChanged.connect(self.newheadOfInterest)

        self.dataFormatSelect.addItems(["0 - RAW_TIMESTAMP", "1 - PLL", "2 - PROCESSED", "3 - QKD"])
        self.dataFormatSelect.currentIndexChanged.connect(self.newDataFormat)


    def update(self):
        data, headNum = self.mdg.manual_data_fetch(formatNum=self.dataFormat)

        # headNum = 1
        # dtype = getFrameDtype(self.dataFormat, keepRaw=False)
        # data = np.zeros((10,), dtype=dtype)
        # for i in range(0, 10):
        #     # ['Addr', 'Energy', 'Global', 'Fine', 'Coarse', 'CorrBit', 'RESERVED']
        #     d = (random.randint(0, 63), 10, 10000, random.randint(1, 50), random.randint(1, 8), 0, 0)
        #     data[i] = d
        if data:
            if (data.size == 0):
                return
        else:
            return

        if headNum == 1:
            self.currentLiveData_H1 = np.append(self.currentLiveData_H1, data)
            if (len(self.currentLiveData_H1) > self.maxSamples):
                self.currentLiveData_H1 = self.currentLiveData_H1[-self.maxSamples:]
        else:
            self.currentLiveData_H0 = np.append(self.currentLiveData_H0, data)
            if (len(self.currentLiveData_H0) > self.maxSamples):
                self.currentLiveData_H0 = self.currentLiveData_H0[-self.maxSamples:]



        self.updateLiveDataTab()
        self.updateSPADTab()
        self.updateOverviewTab()

    def updateLiveDataTab(self):
        self.plotLiveData()

    def updateSPADTab(self):
        image_H0 = processSPADImage(self.currentLiveData_H0)
        if np.sum(image_H0) != 0:
            self.head_0_heatmap.setImage(image_H0, autoLevels=True)

        image_H1 = processSPADImage(self.currentLiveData_H1)
        if np.sum(image_H1) != 0:
            self.head_1_heatmap.setImage(image_H1, autoLevels=True)

    def updateOverviewTab(self):
        pass

    def plotLiveData(self):

        if self.headOfInterest == 1:
            liveDataToUse = self.currentLiveData_H1
        else:
            liveDataToUse = self.currentLiveData_H0
        """Set the data to redraw"""
        selection = self.graphTypeSelect.currentText()
        if self.graphsReady:
            if selection == "Histogram":
                for fieldNumber in range(len(self.monitorList)):
                    field = self.monitorList[fieldNumber]
                    df = processHistogram(liveDataToUse, self.tdcOfInterest, field)
                    self.barGraphs[fieldNumber].setOpts(x=df.x, height=df.y)
            if selection == "Timestamp":
                for fieldNumber in range(len(self.monitorList)):
                    field = self.monitorList[fieldNumber]
                    df = processHistogram(liveDataToUse, self.tdcOfInterest, field)
                    self.barGraphs[fieldNumber].setOpts(x=df.x, height=df.y)

            if selection == "Timestamp Difference":
                hist = self.processDiffTimestamp(liveDataToUse, 50, 8)
                x = np.arange(len(hist))
                self.barGraphs[0].setOpts(x=x, height=hist)


        self.numSamplesLive.display(len(liveDataToUse))


    def clearLiveData(self):
        dtype = getFrameDtype(self.dataFormat, keepRaw=False)
        self.currentLiveData_H0 = np.zeros((0,), dtype=dtype)
        self.currentLiveData_H1 = np.zeros((0,), dtype=dtype)

    def newMaxSamples(self, val):
        self.maxSamples = val

    def newtdcOfInterest(self, val):
        self.tdcOfInterest = val

    def newheadOfInterest(self):
        st = self.headNumberSelect.currentText()
        if st == "H1":
            self.headOfInterest = 1
        else:
            self.headOfInterest = 0

    def newDataFormat(self):
        st = self.dataFormatSelect.currentText()
        if st == "0 - RAW_TIMESTAMP":
            self.dataFormat = 0
        elif st == "1 - PLL":
            self.dataFormat = 1
        elif st == "2 - PROCESSED":
            self.dataFormat = 2
        elif st == "3 - QKD":
            self.dataFormat = 3
        else:
            self.dataFormat = 0

    def selectionChanged(self, i):
        self.graphsReady = False
        selection = self.graphTypeSelect.currentText()

        self.liveDataGraph.clear()
        if selection == "Histogram":
            self.monitorList = ['Fine', 'Coarse']
            self.barGraphs = []
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title="Coarse")
            p.setLabel(axis='left', text='Count')
            p.setLabel(axis='bottom', text='Coarse Code')
            p.addItem(self.barGraphs[-1])
            self.liveDataGraph.nextRow()
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title="Fine")
            p.setLabel(axis='left', text='Count')
            p.setLabel(axis='bottom', text='Fine Code')
            p.addItem(self.barGraphs[-1])
            self.liveDataGraph.nextRow()
        elif selection == "Timestamp":
            self.monitorList = ['Timestamp']
            self.barGraphs = []
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title="Timestamp")
            p.addItem(self.barGraphs[-1])
        elif selection == "TimestampDiff":
            self.barGraphs = []
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title="Timestamp Diff between 2 samples")
            p.addItem(self.barGraphs[-1])
            self.liveDataGraph.nextRow()
        elif selection == "TimestampRel":
            self.barGraphs = []
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title="Timestamp, no global")
            p.addItem(self.barGraphs[-1])
            self.liveDataGraph.nextRow()

        self.graphsReady = True