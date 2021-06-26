import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import h5py
from data_grabber.multicastDataGrabber import MulticastDataGrabber
from processing.dataFormats import getFrameDtype
import random

class LiveViewer:

    def __init__(self, maxSamples=10000):
        super().__init__()
        self.fh = None
        self.win = None
        self._stopping = False
        self.barGraphs = []
        self.datasetSizes = {}
        self.currentGroup = ''
        self.monitorList = []
        self.datasetNames = []
        self.path = None
        self.maxSamples = maxSamples
        self.currSamples = 0

        self.TEMP_GLOBAL = 0
        self.graphsReady = True

        self.x = {}
        self.hist = {}

        dtype = getFrameDtype(0, keepRaw=False)
        self.currentData = np.zeros((0,), dtype=dtype)

        self.mdg = MulticastDataGrabber()

    def start(self, path=None):

        #self.mdg.connectToNetwork()

        self.run()

    def reset_data(self):
        dtype = getFrameDtype(0, keepRaw=False)
        self.currentData = np.zeros((0,), dtype=dtype)

    def processHistogram(self, data):
        hist = np.bincount(data)
        lengthData = len(data)

        return hist, lengthData

    def calcTimestamp(self, glob, fine, coarse, maxFine, maxCoarse):
        # TODO confirm this is the correct LSB
        LSB = 4000 / (maxCoarse * maxFine)
        return ((glob * 4000) + ((coarse*maxFine + fine) * LSB))

    def calcTimestampCode(self, fine, coarse, maxFine):
        return ((coarse*maxFine + fine))

    def processCountRate(self, data):
        global_data = data["Global"]
        energy_data = data["Energy"]
        count_plot = np.zeros((len(global_data) - 1,))

        for i in range(len(global_data) - 1):
            if (global_data[i + 1] - global_data[i]) >= 0:
                # Convert from 4ns steps to KHz
                count_plot[i] = energy_data[i + 1] / ((global_data[i + 1] - global_data[i]) * 4) * 1000000000
            else:  # in the case that the global counter overflows
                time_diff = (0x1FFFFF - global_data[i]) + global_data[i + 1]
                # Convert from 4ns steps to KHz
                count_plot[i] = energy_data[i + 1] / (time_diff * 4) * 1000000000

        return np.mean(count_plot)

    def processDiffTimestamp(self, data, maxFine, maxCoarse):
        global_data = data["Global"]
        timestampDiff = np.zeros((len(global_data) - 1,), dtype="int64")
        for i in range(len(global_data) - 1):
            if (global_data[i + 1] - global_data[i]) >= 0:
                timeDiff = self.calcTimestamp(global_data[i+1], data["Fine"][i+1], data["Coarse"][i+1], maxFine, maxCoarse) - self.calcTimestamp(global_data[i], data["Fine"][i], data["Coarse"][i], maxFine, maxCoarse)
                timestampDiff[i] = timeDiff
            else:  # in the case that the global counter overflows
                timeDiff = self.calcTimestamp(global_data[i+1]+0x1FFFFF, data["Fine"][i+1], data["Coarse"][i+1], maxFine, maxCoarse) - self.calcTimestamp(global_data[i], data["Fine"][i], data["Coarse"][i], maxFine, maxCoarse)
                timestampDiff[i] = timeDiff
        return np.bincount(timestampDiff-np.min(timestampDiff))

    def processRelTimestamp(self, data, maxFine):
        fine_data = data["Fine"]
        timestampRel = np.zeros((len(fine_data),), dtype="int64")
        for i in range(len(timestampRel) - 1):
            timestampRel[i] = self.calcTimestampCode( data["Fine"][i], data["Coarse"][i], maxFine)
        return np.bincount(timestampRel)

    def selectionChanged(self, i):
        self.graphsReady = False
        selection = self.selectedGroup.currentText()

        self.view.clear()
        if selection == "Histogram":
            self.barGraphs = []
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.view.addPlot(title="Coarse")
            p.addItem(self.barGraphs[-1])
            self.view.nextRow()
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.view.addPlot(title="Fine")
            p.addItem(self.barGraphs[-1])
            self.view.nextRow()
        elif selection == "TimestampDiff":
            self.barGraphs = []
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.view.addPlot(title="Timestamp Diff between 2 samples")
            p.addItem(self.barGraphs[-1])
            self.view.nextRow()
        elif selection == "TimestampRel":
            self.barGraphs = []
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.view.addPlot(title="Timestamp, no global")
            p.addItem(self.barGraphs[-1])
            self.view.nextRow()

        self.graphsReady = True

    def run(self):

        self.mw = QtGui.QMainWindow()
        self.mw.resize(800, 800)
        self.view = pg.GraphicsLayoutWidget()  ## GraphicsView with GraphicsLayout inserted by default
        self.mw.setCentralWidget(self.view)

        self._stopping = False

        self.monitorList = ['Fine','Coarse']

        # self.currentData["Fine"] = []
        # self.currentData["Coarse"] = []
        # self.currentData["Global"] = []
        # self.currentData["Energy"] = []
        # self.getDatasetNames()

        self.resetPB = QtGui.QPushButton('Reset')
        self.resetPB.clicked.connect(self.reset_data)
        self.samplesLabel = QtGui.QLabel(text='Samples=')
        self.countRateLabel = QtGui.QLabel(text='CountRate=')
        # t = self.datasetNames
        self.selectedGroup = pg.ComboBox(items=["Histogram", "TimestampDiff", "TimestampRel"])

        self.selectedGroup.currentIndexChanged.connect(self.selectionChanged)
        # self.selectedGroup.setText(self.fh[self.currentGroup].name)

        # self.view.addWidget(radio1, 1, 2, 1, 1)
        self.layout = pg.LayoutWidget()
        self.layout.addWidget(self.resetPB, row=1, col=0, colspan=1)
        self.layout.addWidget(self.samplesLabel, row=1, col=1, colspan=1)
        self.layout.addWidget(self.countRateLabel, row=1, col=2, colspan=1)
        self.layout.addWidget(self.selectedGroup, row=1, col=3, colspan=1)
        self.layout.addWidget(self.view, row=2, col=0, colspan=3)

        self.layout.show()

        #data = self.mdg.manual_data_fetch()
        dtype = getFrameDtype(0, keepRaw=False)
        data = np.zeros((10,), dtype=dtype)
        for i in range(0, 10):
            # ['Addr', 'Energy', 'Global', 'Fine', 'Coarse', 'CorrBit', 'RESERVED']
            d = (0, 10, 50, random.randint(1, 50), random.randint(1, 8), 0, 0)
            data[i] = d

        self.currentData = np.append(self.currentData, data)
        if (len(self.currentData) > self.maxSamples):
            self.currentData = self.currentData[-self.maxSamples:]

        for field in self.monitorList:

            hist, length = self.processHistogram(data[field])
            self.hist[field] = hist
            self.x[field] = np.arange(len(self.hist[field]))
            self.barGraphs.append(pg.BarGraphItem(x=self.x[field], height=self.hist[field], width=0.3, brush='r'))
            #self.mw.setWindowTitle(curr.name)
            p = self.view.addPlot(title=field)
            p.addItem(self.barGraphs[-1])

            self.view.nextRow()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(0)

    def stop(self):
        self._stopping = True
        self.timer.stop()
        self.fh.close()

    def update(self):
        """ Find dataset that was updated last, with priority given to first in monitorList"""

        #data = self.mdg.manual_data_fetch()
        dtype = getFrameDtype(0, keepRaw=False)
        data = np.zeros((10,), dtype=dtype)
        for i in range(0, 10):
            #['Addr', 'Energy', 'Global', 'Fine', 'Coarse', 'CorrBit', 'RESERVED']
            self.TEMP_GLOBAL += 10000
            d = (0, 10, self.TEMP_GLOBAL, random.randint(1, 50), random.randint(1, 8), 0, 0)
            data[i] = d




        if (data == None):
            return

        self.currentData = np.append(self.currentData, data)

        if (len(self.currentData) > self.maxSamples):
            self.currentData = self.currentData[-self.maxSamples:]

        """Set the data to redraw"""
        selection = self.selectedGroup.currentText()
        if self.graphsReady:
            if selection == "Histogram":
                for fieldNumber in range(len(self.monitorList)):
                    field = self.monitorList[fieldNumber]
                    hist, length = self.processHistogram(self.currentData[field])
                    self.hist[field] = hist
                    self.x[field] = np.arange(len(self.hist[field]))
                    self.barGraphs[fieldNumber].setOpts(x=self.x[field], height=self.hist[field])

                    #self.mw.setWindowTitle(curr.name)

            if selection == "TimestampDiff":
                hist = self.processDiffTimestamp(self.currentData, 50, 8)
                x = np.arange(len(hist))
                self.barGraphs[0].setOpts(x=x, height=hist)

            if selection == "TimestampRel":
                hist = self.processRelTimestamp(self.currentData, 50)
                x = np.arange(len(hist))
                self.barGraphs[0].setOpts(x=x, height=hist)

                #self.mw.setWindowTitle(curr.name)


        self.samplesLabel.setText("Samples=" + str(len(self.currentData["Fine"])))
        countRate = self.processCountRate(self.currentData)
        self.countRateLabel.setText("CountRate= %12.2f" % countRate)

        return

    def setBasePath(self, path):
        self.currentGroup = path

    def getDatasetList(self):

        def appendDataset(name, obj):
            if isinstance(obj, h5py.Dataset):
                self.datasetSizes[name] = obj.shape

        self.fh.visititems(appendDataset)

    def getDatasetNames(self):
        def appendDataset(name, obj):
            if name not in self.datasetNames:
                if isinstance(obj, h5py.Group):
                    if all(isinstance(e, h5py.Dataset) for e in obj.values()):
                        self.datasetNames.append('/' + str(name.strip()))

        self.fh.visititems(appendDataset)


def scheduled_task():
    app.quit()


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication([])


    lv = LiveViewer(maxSamples=1000)


    lv.start()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()








