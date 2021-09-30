from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from PyQt5 import QtWidgets, uic
from pyqtgraph import PlotWidget, ColorMap
import pyqtgraph as pg
import pickle

from functions.helper_functions import *
from processing.dataFormats import getFrameDtype
from processing.visuPostProcessing import processHistogram, processHistogramAll, processSPADImage, processCountRate, processTotalCountRate
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

        self.setWindowModality(QtCore.Qt.WindowModal)

        self.connectDialog = ConnectDialogClass()

        self.connectDialog.exec_()

        self.logTextBox = None
        self.setupLogger()

        self.ip = self.connectDialog.ip
        self.port = self.connectDialog.port

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

        self.board = Board(remoteIP=self.ip)

        self.buildView()

        self.mdg = MulticastDataGrabber()
        #self.board = None



    def setupLogger(self):
        self.logTextBox = QTextEditLogger(self.logTextBrowser)
        # You can format what is printed to text box
        self.logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.INFO)

    def connect(self):
        _logger.info("Connecting to network for viewer")
        try:
            self.mdg.connectToNetwork()
            self.board = Board(remoteIP='192.168.0.200')
        except Exception as e:
            _logger.warning("Failed to connect to network with error: " + str(e))





    def buildView(self):

        for field in self.monitorList:
            self.barGraphs.append(pg.BarGraphItem(x=[], height=[], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title=field)
            p.addItem(self.barGraphs[-1])
            self.liveDataGraph.nextRow()

        self.clearDataButton.clicked.connect(self.clearLiveData)

        self.graphTypeSelect.addItems(["Histogram", "Timestamp", "Bin", "TimestampAll"])
        self.graphTypeSelect.currentIndexChanged.connect(self.selectionChanged)

        self.maxSamplesSelect.setMaximum(10 ** 8)
        self.maxSamplesSelect.setKeyboardTracking(False)
        self.maxSamplesSelect.setValue(self.maxSamples)
        self.maxSamplesSelect.valueChanged.connect(self.newMaxSamples)

        self.tdcNumberSelect.setMaximum(192)
        self.tdcNumberSelect.setValue(self.tdcOfInterest)
        self.tdcNumberSelect.valueChanged.connect(self.newtdcOfInterest)

        self.headNumberSelect.addItems(["H0", "H1"])
        self.headNumberSelect.currentIndexChanged.connect(self.newheadOfInterest)

        self.dataFormatSelect.addItems(["0 - RAW_TIMESTAMP", "1 - PLL", "2 - PROCESSED", "3 - QKD"])
        self.dataFormatSelect.currentIndexChanged.connect(self.newDataFormat)

        """ Overview Tab"""

        self.tdc_trig_source_comboBox.addItems(["CORR", "NON_CORR", "EXT", "LASER"])
        self.tdc_trig_source_comboBox.currentIndexChanged.connect(self.tdc_trig_source_changed)
        self.wind_trig_source_comboBox.addItems(["CORR", "NON_CORR", "EXT", "LASER"])
        self.wind_trig_source_comboBox.currentIndexChanged.connect(self.wind_trig_source_changed)

        self.wind_trig_freq_SpinBox.setKeyboardTracking(False)
        self.wind_trig_freq_SpinBox.valueChanged.connect(self.wind_trig_freq_changed)
        self.wind_trig_divider_SpinBox.setKeyboardTracking(False)
        self.wind_trig_divider_SpinBox.valueChanged.connect(self.wind_trig_divider_changed)

        self.tdc_trig_freq_SpinBox.setKeyboardTracking(False)
        self.tdc_trig_freq_SpinBox.valueChanged.connect(self.tdc_trig_freq_changed)
        self.tdc_trig_divider_SpinBox.setKeyboardTracking(False)
        self.tdc_trig_divider_SpinBox.valueChanged.connect(self.tdc_trig_divider_changed)

        self.pll_fast_h0_SpinBox.setKeyboardTracking(False)
        self.pll_fast_h0_SpinBox.valueChanged.connect(lambda p: self.board.fast_oscillator_head_0.set_frequency(p))
        self.pll_slow_h0_SpinBox.setKeyboardTracking(False)
        self.pll_slow_h0_SpinBox.valueChanged.connect(lambda p: self.board.slow_oscillator_head_0.set_frequency(p))
        self.pll_fast_h1_SpinBox.setKeyboardTracking(False)
        self.pll_fast_h1_SpinBox.valueChanged.connect(lambda p: self.board.fast_oscillator_head_1.set_frequency(p))
        self.pll_slow_h1_SpinBox.setKeyboardTracking(False)
        self.pll_slow_h1_SpinBox.valueChanged.connect(lambda p: self.board.slow_oscillator_head_1.set_frequency(p))

        self.dac_fast_h0_SpinBox.setKeyboardTracking(False)
        self.dac_fast_h0_SpinBox.valueChanged.connect(self.board.v_fast_head_0.set_voltage)
        self.dac_slow_h0_SpinBox.setKeyboardTracking(False)
        self.dac_slow_h0_SpinBox.valueChanged.connect(self.board.v_slow_head_0.set_voltage)
        self.dac_fast_h1_SpinBox.setKeyboardTracking(False)
        self.dac_fast_h1_SpinBox.valueChanged.connect(self.board.v_fast_head_1.set_voltage)
        self.dac_slow_h1_SpinBox.setKeyboardTracking(False)
        self.dac_slow_h1_SpinBox.valueChanged.connect(self.board.v_slow_head_1.set_voltage)

        self.tdc_trig_delay_h0_SpinBox.setKeyboardTracking(False)
        self.tdc_trig_delay_h0_SpinBox.valueChanged.connect(self.trigger_h0_delay)
        self.tdc_trig_delay_h1_SpinBox.setKeyboardTracking(False)
        self.tdc_trig_delay_h1_SpinBox.valueChanged.connect(self.trigger_h1_delay)
        self.wind_trig_delay_h0_SpinBox.setKeyboardTracking(False)
        self.wind_trig_delay_h0_SpinBox.valueChanged.connect(self.window_h0_delay)
        self.wind_trig_delay_h1_SpinBox.setKeyboardTracking(False)
        self.wind_trig_delay_h1_SpinBox.valueChanged.connect(self.window_h1_delay)




        self.pll_enable_h0_checkBox.stateChanged.connect(self.pll_enable_h0_changed)
        self.pll_enable_h1_checkBox.stateChanged.connect(self.pll_enable_h1_changed)

        self.window_is_stop_h0_checkBox.stateChanged.connect(self.window_is_stop_h0_changed)
        self.window_is_stop_h0_checkBox.stateChanged.connect(self.window_is_stop_h1_changed)


        """ ASIC TAB"""

        self.reset_h0_pushButton.clicked.connect(self.reset_h0)
        self.reset_h1_pushButton.clicked.connect(self.board.asic_head_1.reset)

        self.threshold_time_trigger_h0_spinBox.setKeyboardTracking(False)
        self.threshold_time_trigger_h0_spinBox.valueChanged.connect(self.threshold_time_changed_h0)

        self.threshold_time_trigger_h1_spinBox.setKeyboardTracking(False)
        self.threshold_time_trigger_h1_spinBox.valueChanged.connect(self.threshold_time_changed_h1)

        self.laser_trigger_thresh_spinBox.setKeyboardTracking(False)
        self.laser_trigger_thresh_spinBox.valueChanged.connect(self.laser_trigger_thres_changed)

        self.disable_all_quench_h0_pushButton.clicked.connect(self.disable_all_quench_h0)
        self.disable_all_quench_h1_pushButton.clicked.connect(self.disable_all_quench_h1)
        self.enable_all_quench_h0_pushButton.clicked.connect(self.enable_all_quench_h0)
        self.enable_all_quench_h1_pushButton.clicked.connect(self.enable_all_quench_h1)

        self.disable_all_tdc_h0_pushButton.clicked.connect(self.disable_all_tdc_h0)
        self.disable_all_tdc_h1_pushButton.clicked.connect(self.board.asic_head_1.disable_all_tdc)
        self.enable_all_tdc_h0_pushButton.clicked.connect(self.enable_all_tdc_h0)
        self.enable_all_tdc_h1_pushButton.clicked.connect(self.board.asic_head_1.enable_all_tdc)

        self.disable_all_ext_trigger_h0_pushButton.clicked.connect(self.disable_all_ext_trigger_h0)
        self.disable_all_ext_trigger_h1_pushButton.clicked.connect(self.board.asic_head_1.disable_all_ext_trigger)
        self.enable_all_ext_trigger_h0_pushButton.clicked.connect(self.enable_all_ext_trigger_h0)
        self.enable_all_ext_trigger_h1_pushButton.clicked.connect(self.board.asic_head_1.enable_all_ext_trigger)

        self.array_select_h0_comboBox.addItems(["0 - ARRAY 0 (14x14)", "1 - ARRAY 1 (8x8) "])
        self.array_select_h0_comboBox.currentIndexChanged.connect(self.mux_select_h0)

        self.array_select_h1_comboBox.addItems(["0 - ARRAY 0 (14x14)", "1 - ARRAY 1 (8x8) "])
        self.array_select_h1_comboBox.currentIndexChanged.connect(self.mux_select_h1)

        self.post_processing_select_h0_comboBox.addItems(["0 - RAW", "1 - TIME_CONVERSION", "2 - SORTED", "3 - DARK_COUNT_FILTERED", "4 - BLUE", "5 - GATED_COUNT", "6 - GATED_BITMAP", "7 - GATED_EVENT_DETECT", "8 - ZPP", "9 - NOT USED", "10 - QKD_ABS_TIMESTAMP", "11 - QKD_TIME_BIN", "12 - QKD_DCA_FLAG"])
        self.post_processing_select_h0_comboBox.currentIndexChanged.connect(self.mux_select_h0)

        self.post_processing_select_h1_comboBox.addItems(["0 - RAW", "1 - TIME_CONVERSION", "2 - SORTED", "3 - DARK_COUNT_FILTERED", "4 - BLUE", "5 - GATED_COUNT", "6 - GATED_BITMAP", "7 - GATED_EVENT_DETECT", "8 - ZPP", "9 - NOT USED", "10 - QKD_ABS_TIMESTAMP", "11 - QKD_TIME_BIN", "12 - QKD_DCA_FLAG"])
        self.post_processing_select_h1_comboBox.currentIndexChanged.connect(self.mux_select_h1)

        self.trigger_type_h0_comboBox.addItems(["0 - TIME_DRIVEN", "1 - EVENT_DRIVEN", "2 - WINDOW_DRIVEN"])
        self.trigger_type_h0_comboBox.currentIndexChanged.connect(self.trigger_type_h0)

        self.trigger_type_h1_comboBox.addItems(["0 - TIME_DRIVEN", "1 - EVENT_DRIVEN", "2 - WINDOW_DRIVEN"])
        self.trigger_type_h1_comboBox.currentIndexChanged.connect(self.trigger_type_h1)

        self.recharge_h0_spinBox.setKeyboardTracking(False)
        self.recharge_h0_spinBox.valueChanged.connect(self.recharge_current_h0)

        self.holdoff_h0_spinBox.setKeyboardTracking(False)
        self.holdoff_h0_spinBox.valueChanged.connect(self.holdoff_current_h0)

        self.v_comp_h0_spinBox.setKeyboardTracking(False)
        self.v_comp_h0_spinBox.valueChanged.connect(self.comparator_voltage_h0)

        self.window_length_h0_SpinBox.setKeyboardTracking(False)
        self.window_length_h0_SpinBox.valueChanged.connect(self.window_length_h0_changed)

        self.window_length_h1_SpinBox.setKeyboardTracking(False)
        self.window_length_h1_SpinBox.valueChanged.connect(self.window_length_h1_changed)

        self.correction_type_h0_comboBox.addItems(["lin", "lin_bias", "lin_bias_slope"])
        self.correction_type_h1_comboBox.addItems(["lin", "lin_bias", "lin_bias_slope"])

        self.apply_correction_h0_pushButtion.clicked.connect(self.apply_corrections)

        self.bound_0_h0_spinBox.setKeyboardTracking(False)
        self.bound_0_h0_spinBox.valueChanged.connect(self.bound_0_h0_changed)
        self.bound_1_h0_spinBox.setKeyboardTracking(False)
        self.bound_1_h0_spinBox.valueChanged.connect(self.bound_1_h0_changed)
        self.bound_2_h0_spinBox.setKeyboardTracking(False)
        self.bound_2_h0_spinBox.valueChanged.connect(self.bound_2_h0_changed)
        self.bound_3_h0_spinBox.setKeyboardTracking(False)
        self.bound_3_h0_spinBox.valueChanged.connect(self.bound_3_h0_changed)


        time.sleep(1)

        self.updateOverviewTab()

    def laser_trigger_thres_changed(self, value):
        self.board.laser_threshold.set_voltage(value)

    def recharge_current_h0(self, value):
        self.board.recharge_current.set_current(value)

    def holdoff_current_h0(self, value):
        self.board.holdoff_current.set_current(value)

    def comparator_voltage_h0(self, value):
        self.board.comparator_threshold.set_voltage((value/3.3)*5)

    def disable_all_quench_h0(self):
        self.board.asic_head_0.disable_all_quench()

    def disable_all_quench_h1(self):
        self.board.asic_head_1.disable_all_quench()

    def enable_all_quench_h0(self):
        self.board.asic_head_0.enable_all_quench()

    def enable_all_quench_h1(self):
        self.board.asic_head_1.enable_all_quench()

    def disable_all_tdc_h0(self):
        self.board.asic_head_0.disable_all_tdc()

    def enable_all_tdc_h0(self):
        self.board.asic_head_0.enable_all_tdc()


    def enable_all_ext_trigger_h0(self):
        self.board.asic_head_0.enable_all_ext_trigger()

    def disable_all_ext_trigger_h0(self):
        self.board.asic_head_0.disable_all_ext_trigger()

    def update(self):
        data, headNum = self.mdg.manual_data_fetch(formatNum=self.dataFormat)

        # headNum = 0
        # dtype = getFrameDtype(self.dataFormat, keepRaw=False)
        # data = np.zeros((10,), dtype=dtype)
        # for i in range(0, 10):
        #     # ['Addr', 'Energy', 'Global', 'Fine', 'Coarse', 'CorrBit', 'RESERVED']
        #     d = (random.randint(0, 63), 10, 10000, random.randint(1, 50), random.randint(1, 8), 0, 0)
        #     data[i] = d

        if data is not None:
            if (data.size != 0):
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



    def updateLiveDataTab(self):
        self.plotLiveData()

    def updateSPADTab(self):
        image_H0 = processSPADImage(self.currentLiveData_H0)
        if np.sum(image_H0) != 0:
            self.head_0_heatmap.setImage(image_H0, autoLevels=True)

        cr_h0 = processTotalCountRate(self.currentLiveData_H0)

        self.totalCount_H0.display(cr_h0)

        image_H1 = processSPADImage(self.currentLiveData_H1)
        if np.sum(image_H1) != 0:
            self.head_1_heatmap.setImage(image_H1, autoLevels=True)

        cr_h1 = processTotalCountRate(self.currentLiveData_H1)
        self.totalCount_H1.display(cr_h1)

    def updateOverviewTab(self):
        status = self.board.getStatus()

        self.pll_fast_h0_SpinBox.setValue(status["fast_oscillator_head_0"]["frequency"])
        self.pll_slow_h0_SpinBox.setValue(status["slow_oscillator_head_0"]["frequency"])
        self.pll_fast_h1_SpinBox.setValue(status["fast_oscillator_head_1"]["frequency"])
        self.pll_slow_h1_SpinBox.setValue(status["slow_oscillator_head_1"]["frequency"])

        self.dac_fast_h0_SpinBox.setValue(status["v_fast_head_0"]["volt"])
        self.dac_slow_h0_SpinBox.setValue(status["v_slow_head_0"]["volt"])
        self.dac_fast_h1_SpinBox.setValue(status["v_fast_head_1"]["volt"])
        self.dac_slow_h1_SpinBox.setValue(status["v_slow_head_1"]["volt"])

        self.tdc_trig_divider_SpinBox.setValue(status["trigger_divider"]["divider"])
        self.wind_trig_divider_SpinBox.setValue(status["window_divider"]["divider"])

        if status["trigger_divider"]["mux_sel"] == 0:
            self.tdc_trig_source_comboBox.setCurrentText("NON_CORR")
        elif status["trigger_divider"]["mux_sel"] == 1:
            self.tdc_trig_source_comboBox.setCurrentText("CORR")

        if status["window_divider"]["mux_sel"] == 0:
            self.wind_trig_source_comboBox.setCurrentText("NON_CORR")
        elif status["window_divider"]["mux_sel"] == 1:
            self.wind_trig_source_comboBox.setCurrentText("CORR")

        tdc_trig_source = self.tdc_trig_source_comboBox.currentText()
        if tdc_trig_source == "CORR":
            self.tdc_trig_freq_SpinBox.setValue(status["pll"]["frequency"])
        elif tdc_trig_source == "NON_CORR":
            self.tdc_trig_freq_SpinBox.setValue(status["trigger_oscillator"]["frequency"])

        wind_trig_source = self.wind_trig_source_comboBox.currentText()
        if wind_trig_source == "CORR":
            self.wind_trig_freq_SpinBox.setValue(status["pll"]["frequency"])
        elif wind_trig_source == "NON_CORR":
            self.wind_trig_freq_SpinBox.setValue(status["window_oscillator"]["frequency"])




        #_logger.info("Updated Overview Tab")


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
            if selection == "TimestampAll":
                for fieldNumber in range(len(self.monitorList)):
                    field = self.monitorList[fieldNumber]
                    df = processHistogramAll(liveDataToUse, field)
                    self.barGraphs[fieldNumber].setOpts(x=df.x, height=df.y)
            if selection == "Bin":
                for fieldNumber in range(len(self.monitorList)):
                    field = self.monitorList[fieldNumber]
                    df = processHistogram(liveDataToUse, self.tdcOfInterest, field)
                    self.barGraphs[fieldNumber].setOpts(x=df.x, height=df.y)

            if selection == "Timestamp Difference":
                hist = self.processDiffTimestamp(liveDataToUse, 50, 8)
                x = np.arange(len(hist))
                self.barGraphs[0].setOpts(x=x, height=hist)


        self.numSamplesLive.display(liveDataToUse.size)

        self.countRateNumber.display(processCountRate(liveDataToUse, self.tdcOfInterest))


    def clearLiveData(self):
        dtype = getFrameDtype(self.dataFormat, keepRaw=False)
        self.currentLiveData_H0 = np.zeros((0,), dtype=dtype)
        self.currentLiveData_H1 = np.zeros((0,), dtype=dtype)

    def newMaxSamples(self, val):
        self.maxSamples = np.int64(val)

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

        _logger.info("Changed data format to : " + str(st))

        self.clearLiveData()

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
        elif selection == "TimestampAll":
            self.monitorList = ['TimestampAll']
            self.barGraphs = []
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title="TimestampAll")
            p.addItem(self.barGraphs[-1])
        elif selection == "Bin":
            self.monitorList = ['Bin']
            self.barGraphs = []
            self.barGraphs.append(pg.BarGraphItem(x=[0], height=[0], width=0.3, brush='r'))
            p = self.liveDataGraph.addPlot(title="Bin")
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

        _logger.info("Changed graph type to : " + str(selection))



    def tdc_trig_source_changed(self):
        selection = self.tdc_trig_source_comboBox.currentText()

        try:

            if selection == "CORR":
                div = self.tdc_trig_divider_SpinBox.value()
                self.board.trigger_divider.set_divider(div, Divider.MUX_CORR)
                self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
                self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
            elif selection == "NON_CORR":
                div = self.tdc_trig_divider_SpinBox.value()
                self.board.trigger_divider.set_divider(div, Divider.MUX_NOT_CORR)
                self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
                self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)
                self.board.trigger_delay_head_0.set_delay_code(0)
            elif selection == "EXT":
                self.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)
                self.board.mux_trigger_external.select_input(MUX.EXTERNAL_INPUT)
            elif selection == "LASER":
                self.board.mux_coarse_delay.select_input(MUX.MONOSTABLE)
                self.board.mux_trigger_laser.select_input(MUX.LASER_INPUT)
                self.board.mux_trigger_external.select_input(MUX.PCB_INPUT)

        except Exception as e:
            _logger.warning("Could not set frequency or divider due to the following error:")
            _logger.warning(e)

        _logger.info("Changed TDC trig source to to : " + str(selection))

        self.updateOverviewTab()


    def wind_trig_source_changed(self):
        selection = self.wind_trig_source_comboBox.currentText()

        try:

            if selection == "CORR":
                div = self.wind_trig_divider_SpinBox.value()
                self.board.window_divider.set_divider(div, Divider.MUX_CORR)
                self.board.mux_window_laser.select_input(MUX.DIVIDER_INPUT)
                self.board.mux_window_external.select_input(MUX.PCB_INPUT)
            elif selection == "NON_CORR":
                div = self.wind_trig_divider_SpinBox.value()
                self.board.window_divider.set_divider(div, Divider.MUX_NOT_CORR)
                self.board.mux_window_laser.select_input(MUX.DIVIDER_INPUT)
                self.board.mux_window_external.select_input(MUX.PCB_INPUT)
            elif selection == "EXT":
                self.board.mux_window_laser.select_input(MUX.DIVIDER_INPUT)
                self.board.mux_window_external.select_input(MUX.EXTERNAL_INPUT)
            elif selection == "LASER":
                self.board.mux_coarse_delay.select_input(MUX.MONOSTABLE)
                self.board.mux_window_laser.select_input(MUX.LASER_INPUT)
                self.board.mux_window_external.select_input(MUX.PCB_INPUT)

        except Exception as e:
            _logger.warning("Could not set frequency or divider due to the following error:")
            _logger.warning(e)

        _logger.info("Changed Window trig source to to : " + str(selection))
        self.updateOverviewTab()


    def wind_trig_freq_changed(self, val):
        selection = self.wind_trig_source_comboBox.currentText()
        if selection == "CORR":
            try:
                self.board.pll.set_frequencies(val, val)
            except Exception as e:
                _logger.warning("Could not set frequency due to the following error:")
                _logger.warning(e)
        elif selection == "NON_CORR":
            try:
                self.board.window_oscillator.set_frequency(val)
            except Exception as e:
                _logger.warning("Could not set frequency due to the following error:")
                _logger.warning(e)

        self.updateOverviewTab()

    def wind_trig_divider_changed(self, val):
        selection = self.wind_trig_source_comboBox.currentText()
        if selection == "CORR":
            try:
                self.board.window_divider.set_divider(val, Divider.MUX_CORR)
            except Exception as e:
                _logger.warning("Could not set frequency due to the following error:")
                _logger.warning(e)
        elif selection == "NON_CORR":
            try:
                self.board.window_divider.set_divider(val, Divider.MUX_NOT_CORR)
            except Exception as e:
                _logger.warning("Could not set frequency due to the following error:")
                _logger.warning(e)

        self.updateOverviewTab()

    def tdc_trig_freq_changed(self, val):
        selection = self.tdc_trig_source_comboBox.currentText()
        if selection == "CORR":
            try:
                self.board.pll.set_frequencies(val, val)
            except Exception as e:
                _logger.warning("Could not set frequency due to the following error:")
                _logger.warning(e)

        elif selection == "NON_CORR":
            try:
                self.board.trigger_oscillator.set_frequency(val)
            except Exception as e:
                _logger.warning("Could not set frequency due to the following error:")
                _logger.warning(e)

        self.updateOverviewTab()

    def tdc_trig_divider_changed(self, val):
        selection = self.wind_trig_source_comboBox.currentText()
        if selection == "CORR":
            try:
                self.board.trigger_divider.set_divider(val, Divider.MUX_CORR)
            except Exception as e:
                _logger.warning("Could not set frequency due to the following error:")
                _logger.warning(e)
        elif selection == "NON_CORR":
            try:
                self.board.trigger_divider.set_divider(val, Divider.MUX_NOT_CORR)
            except Exception as e:
                _logger.warning("Could not set frequency due to the following error:")
                _logger.warning(e)

        self.updateOverviewTab()

    def reset_h0(self):
        self.board.asic_head_0.reset()

    def pll_enable_h0_changed(self, state):
        if state ==0:
            self.board.b.ICYSHSR1.PLL_ENABLE(0, 0, 0)
        else:
            self.board.b.ICYSHSR1.PLL_ENABLE(0, 1, 0)

    def pll_enable_h1_changed(self, state):
        if state == 0:
            self.board.b.ICYSHSR1.PLL_ENABLE(1, 0, 0)
        else:
            self.board.b.ICYSHSR1.PLL_ENABLE(1, 1, 0)

    def window_is_stop_h0_changed(self, state):
        if state == 0:
            self.board.asic_head_0.clock_is_stop()
        else:
            self.board.asic_head_0.window_is_stop()

    def window_is_stop_h1_changed(self, state):
        if state == 0:
            self.board.asic_head_1.clock_is_stop()
        else:
            self.board.asic_head_1.window_is_stop()

    def window_length_h0_changed(self, window_length):
        self.board.asic_head_0.set_window_size(int(window_length))

    def window_length_h1_changed(self, window_length):
        self.board.asic_head_1.set_window_size(int(window_length))


    def mux_select_h0(self):
        pp = self.post_processing_select_h0_comboBox.currentIndex()
        array = self.array_select_h0_comboBox.currentIndex()

        self.board.asic_head_0.mux_select(array, pp)

    def mux_select_h1(self):
        pp = self.post_processing_select_h1_comboBox.currentIndex()
        array = self.array_select_h1_comboBox.currentIndex()

        self.board.asic_head_1.mux_select(array, pp)

    def trigger_type_h0(self):
        trigger_type = self.trigger_type_h0_comboBox.currentIndex()

        if trigger_type == 0:
            self.board.asic_head_0.set_trigger_type(0)
            self.threshold_time_trigger_h0_spinBox.setValue(self.board.b.ICYSHSR1.TRIGGER_TIME_DRIVEN_PERIOD(0, 0))
        elif trigger_type == 1:
            self.board.asic_head_0.set_trigger_type(1)
            self.threshold_time_trigger_h0_spinBox.setValue(self.board.b.ICYSHSR1.TRIGGER_EVENT_DRIVEN_COLUMN_THRESHOLD(0, 0))
        elif trigger_type == 2:
            self.board.asic_head_0.set_trigger_type(0x10)
            self.threshold_time_trigger_h0_spinBox.setValue(self.board.b.ICYSHSR1.TRIGGER_WINDOW_DRIVEN_THRESHOLD(0, 0))

    def trigger_type_h1(self):
        trigger_type = self.trigger_type_h1_comboBox.currentIndex()

        if trigger_type == 0:
            self.board.asic_head_1.set_trigger_type(0)
            self.threshold_time_trigger_h1_spinBox.setValue(self.board.b.ICYSHSR1.TRIGGER_TIME_DRIVEN_PERIOD(1, 0))
        elif trigger_type == 1:
            self.board.asic_head_1.set_trigger_type(1)
            self.threshold_time_trigger_h1_spinBox.setValue(self.board.b.ICYSHSR1.TRIGGER_EVENT_DRIVEN_COLUMN_THRESHOLD(1, 0))
        elif trigger_type == 2:
            self.board.asic_head_1.set_trigger_type(0x10)
            self.threshold_time_trigger_h1_spinBox.setValue(self.board.b.ICYSHSR1.TRIGGER_WINDOW_DRIVEN_THRESHOLD(1, 0))


    def threshold_time_changed_h0(self, val):
        trigger_type = self.trigger_type_h0_comboBox.currentIndex()

        if trigger_type == 0:
            self.board.asic_head_0.set_time_driven_period(val)
        elif trigger_type == 1:
            self.board.b.ICYSHSR1.TRIGGER_EVENT_DRIVEN_COLUMN_THRESHOLD(0, val, 0)
        elif trigger_type == 2:
            self.board.b.ICYSHSR1.TRIGGER_WINDOW_DRIVEN_THRESHOLD(0, val, 0)

    def threshold_time_changed_h1(self, val):
        trigger_type = self.trigger_type_h1_comboBox.currentIndex()

        if trigger_type == 0:
            self.board.asic_head_1.set_trigger_type(0)
        elif trigger_type == 1:
            self.board.b.ICYSHSR1.TRIGGER_EVENT_DRIVEN_COLUMN_THRESHOLD(1, val, 0)
        elif trigger_type == 2:
            self.board.b.ICYSHSR1.TRIGGER_WINDOW_DRIVEN_THRESHOLD(1, val, 0)


    def apply_corrections(self):

        array = self.array_select_h0_comboBox.currentIndex()
        head  = self.asic_number_h0_spinBox.value()
        freq = 255
        type = self.correction_type_h0_comboBox.currentText()

        # with open('skew.pickle', 'rb') as f:
        #     skew_corr = pickle.load(f)
        #     for tdc in range(len(skew_corr)):
        #         self.board.asic_head_0.set_skew_correction(array, tdc*4, skew_corr[tdc])

        corr_filename = "H{0}_M{1}_F{2}_{3}.pickle".format(int(head), int(array), int(freq), type)

        with open(corr_filename, 'rb') as f:
            coefficients = pickle.load(f)
            for tdc_id in coefficients:
                coarse_corr = int(coefficients[tdc_id][0] * 8)
                fine_corr = int(coefficients[tdc_id][1] * 16)
                bias_lookup = np.clip((coefficients[tdc_id][2]+128).astype(int), 0, 255)
                slope_lookup = np.clip((coefficients[tdc_id][3]*8).astype(int), 0, 15)
                self.board.asic_head_0.set_coarse_correction(array, tdc_id, coarse_corr)
                self.board.asic_head_0.set_fine_correction(array, tdc_id, fine_corr)

                if ((type == "lin_bias") or (type == "lin_bias_slope")):
                    self.board.asic_head_0.set_lookup_tables(array, tdc_id, bias_lookup, slope_lookup)


    def bound_0_h0_changed(self, val):
        self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_0(0, int(val), 0)

    def bound_1_h0_changed(self, val):
        self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_0_1(0, int(val), 0)

    def bound_2_h0_changed(self, val):
        self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_1_2(0, int(val), 0)

    def bound_3_h0_changed(self, val):
        self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_2(0, int(val), 0)

    def trigger_h0_delay(self, val):
        self.board.trigger_delay_head_0.set_delay(val)

    def trigger_h1_delay(self, val):
        self.board.trigger_delay_head_1.set_delay(val)

    def window_h0_delay(self, val):
        self.board.window_delay_head_0.set_delay(val)

    def window_h1_delay(self, val):
        self.board.window_delay_head_1.set_delay(val)

class ConnectDialogClass(QtWidgets.QDialog):
    def __init__(self):
        super(ConnectDialogClass, self).__init__()
        uic.loadUi("connect.ui", self)

        self.ip = None
        self.port = None


        self.buttonBox.rejected.connect(self.quitProgram)
        self.buttonBox.accepted.connect(self.storeSettings)

    def quitProgram(self):
        exit()


    def storeSettings(self):
        self.ip = self.ip_setting.text()
        self.port = int(self.port_setting.text())


