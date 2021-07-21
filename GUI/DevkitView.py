from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from PyQt5 import QtWidgets, uic
from pyqtgraph import PlotWidget, ColorMap
import pyqtgraph as pg

from processing.dataFormats import getFrameDtype
from processing.visuPostProcessing import processHistogram, processSPADImage
import random

class DevkitView(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(DevkitView, self).__init__(*args, **kwargs)

        # Load the UI Page
        uic.loadUi('MainWindow.ui', self)

        dtype = getFrameDtype(0, keepRaw=False)
        self.currentLiveData = np.zeros((0,), dtype=dtype)


        self.maxSamples = 5000
        self.x = {}
        self.hist = {}
        self.barGraphs = []

        self.monitorList = ['Fine', 'Coarse']
        self.graphsReady = True

        self.buildView()

    def connect(self):
        pass

    def buildView(self):

        for field in self.monitorList:
            self.hist[field] = []
            self.x[field] = []
            self.barGraphs.append(pg.BarGraphItem(x=self.x[field], height=self.hist[field], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title=field)
            p.addItem(self.barGraphs[-1])
            self.liveDataGraph.nextRow()

        self.clearDataButton.clicked.connect(self.clearLiveData)

        self.graphTypeSelect.addItems(["Histogram", "Timestamp Difference", "Timestamp"])
        self.graphTypeSelect.currentIndexChanged.connect(self.selectionChanged)


    def update(self):
        # data = self.mdg.manual_data_fetch()
        dtype = getFrameDtype(0, keepRaw=False)
        data = np.zeros((10,), dtype=dtype)
        for i in range(0, 10):
            # ['Addr', 'Energy', 'Global', 'Fine', 'Coarse', 'CorrBit', 'RESERVED']
            d = (random.randint(0, 63), 10, 10000, random.randint(1, 50), random.randint(1, 8), 0, 0)
            data[i] = d

        if (data == None):
            return

        self.currentLiveData = np.append(self.currentLiveData, data)

        if (len(self.currentLiveData) > self.maxSamples):
            self.currentLiveData = self.currentLiveData[-self.maxSamples:]

        self.updateLiveDataTab()
        self.updateSPADTab()
        self.updateOverviewTab()

    def updateLiveDataTab(self):
        self.plotLiveData()

    def updateSPADTab(self):
        #self.head_0_heatmap.show()
        image = processSPADImage(self.currentLiveData)
        self.head_0_heatmap.setImage(image)

    def updateOverviewTab(self):
        pass

    def plotLiveData(self):
        """Set the data to redraw"""
        selection = self.graphTypeSelect.currentText()
        if self.graphsReady:
            if selection == "Histogram":
                for fieldNumber in range(len(self.monitorList)):
                    field = self.monitorList[fieldNumber]
                    df = processHistogram(self.currentLiveData, 0, field)
                    self.barGraphs[fieldNumber].setOpts(x=df.x, height=df.y)

            if selection == "Timestamp Difference":
                hist = self.processDiffTimestamp(self.currentLiveData, 50, 8)
                x = np.arange(len(hist))
                self.barGraphs[0].setOpts(x=x, height=hist)

            if selection == "Timestamp":
                hist = self.processTimestamp(self.currentLiveData, 50)
                x = np.arange(len(hist))
                self.barGraphs[0].setOpts(x=x, height=hist)


        self.numSamplesLive.display(len(self.currentLiveData))


    def clearLiveData(self):
        dtype = getFrameDtype(0, keepRaw=False)
        self.currentLiveData = np.zeros((0,), dtype=dtype)

    def selectionChanged(self, i):
        self.graphsReady = False
        selection = self.graphTypeSelect.currentText()

        self.liveDataGraph.clear()
        if selection == "Histogram":
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