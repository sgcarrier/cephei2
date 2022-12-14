from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from PyQt5 import QtWidgets, uic
from pyqtgraph import PlotWidget, ColorMap
import pyqtgraph as pg
import pickle
from scipy import stats
import os

from processing.visuPostProcessing import calcMaxFine, calcMaxCoarse
#from processing.get_TDC_skew import calcSkewCoef
#from processing.ICYSHSR1_get_coef import calcCoef

import h5py

from functions.helper_functions import *
from processing.dataFormats import getFrameDtype
from processing.visuPostProcessing import processHistogram, processHistogramAll, processSPADImage, processCountRate, processTotalCountRate, calcPeak
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

        self.__recording = False
        self.currentHDFFile = None
        self.maxSamples = 1000
        self.tdcOfInterest = 0
        self.headOfInterest = 0
        self.barGraphs = []

        self.monitorList = ['Fine', 'Coarse']
        self.graphsReady = True

        self.last_time = time.time()

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
        self.dac_fast_h0_SpinBox.valueChanged.connect(self.set_dac_fast_h0)
        self.dac_slow_h0_SpinBox.setKeyboardTracking(False)
        self.dac_slow_h0_SpinBox.valueChanged.connect(self.set_dac_slow_h0)
        self.dac_fast_h1_SpinBox.setKeyboardTracking(False)
        self.dac_fast_h1_SpinBox.valueChanged.connect(self.set_dac_fast_h1)
        self.dac_slow_h1_SpinBox.setKeyboardTracking(False)
        self.dac_slow_h1_SpinBox.valueChanged.connect(self.set_dac_slow_h1)

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
        


        self.read_untriggered_checkBox.stateChanged.connect(self.read_untriggered_h0_changed)


        """ ASIC TAB"""

        self.reset_h0_pushButton.clicked.connect(self.reset_h0)
        self.reset_h1_pushButton.clicked.connect(self.board.asic_head_1.reset)

        self.threshold_time_trigger_h0_spinBox.setKeyboardTracking(False)
        self.threshold_time_trigger_h0_spinBox.valueChanged.connect(self.threshold_time_changed_h0)

        self.threshold_time_trigger_h1_spinBox.setKeyboardTracking(False)
        self.threshold_time_trigger_h1_spinBox.valueChanged.connect(self.threshold_time_changed_h1)

        self.laser_trigger_thresh_spinBox.setKeyboardTracking(False)
        self.laser_trigger_thresh_spinBox.valueChanged.connect(self.laser_trigger_thres_changed)

        self.laser_trigger_h0_inverted_checkBox.stateChanged.connect(self.laser_trigger_thres_inverted_changed)

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

        self.v_comp_h0_doubleSpinBox.setKeyboardTracking(False)
        self.v_comp_h0_doubleSpinBox.valueChanged.connect(self.comparator_voltage_h0)

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

        self.disable_all_quench_but_pushButton.clicked.connect(self.disable_all_quench_but_h0)

        self.dca_threshold_h0_spinBox.setKeyboardTracking(False)
        self.dca_threshold_h0_spinBox.valueChanged.connect(self.set_DCA_threshold_h0)

        """Recording Tab"""

        self.record_start_pushButton.clicked.connect(self.start_recording)

        time.sleep(1)

        self.updateOverviewTab()

    def start_recording(self):
        self.__recording = True
        self.time_record_start = time.time()
        _logger.info("Started Recording")

    def disable_all_quench_but_h0(self):
        quench = self.quench_exception_h0_spinBox.value()
        array = self.array_select_h0_comboBox.currentIndex()
        self.board.asic_head_0.disable_all_quench_but(array, [quench])

    def read_untriggered_h0_changed(self, state):
        if state == 0:
            self.board.b.ICYSHSR1.READ_UNTRIGGERED_TDCS(0, 0, 0)
        else:
            self.board.b.ICYSHSR1.READ_UNTRIGGERED_TDCS(0, 1, 0)


    def set_dac_fast_h0(self, val):
        self.board.v_fast_head_0.set_voltage(val)


    def set_dac_slow_h0(self, val):
        self.board.v_slow_head_0.set_voltage(val)

    def set_dac_fast_h1(self, val):
        self.board.v_fast_head_1.set_voltage(val)

    def set_dac_slow_h1(self, val):
        self.board.v_slow_head_1.set_voltage(val)

    def laser_trigger_thres_changed(self, value):
        self.board.laser_threshold.set_voltage(value)

    def laser_trigger_thres_inverted_changed(self, state):
        if state == 0:
            self.board.mux_laser_polarity.select_input(MUX.NON_INVERTED)
        else:
            self.board.mux_laser_polarity.select_input(MUX.INVERTED)

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
                if self.__recording:
                    self.saveDataToHDF(headNum, data)
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
                self.autoChangeWindowWithSync()

    def autoChangeWindowWithSync(self):
        current_time = time.time()
        if self.activate_sync_pixel_checkBox.isChecked() and ((current_time - self.last_time) > 10) :
            pix_addr = self.sync_pixel_addr_h0_spinBox.value()
            peak = calcPeak(self.currentLiveData_H0, pix_addr, 4)
            self.last_time = current_time
            if peak != -1:
                objective = self.center_window_delay_spinBox.value()
                shift = int(objective - peak)
                current_delay = self.wind_trig_delay_h0_SpinBox.value()
                new_delay = current_delay + shift
                if new_delay < 0:
                    new_delay = 0

                self.wind_trig_delay_h0_SpinBox.setValue(new_delay)



    def saveDataToHDF(self, headNum, data):
        filename = self.hdf_filename_lineEdit.text()
        path = self.hdf_path_lineEdit.text()
        samples = self.hdf_samples_spinBox.value()

        self.hdf_recording_progressBar.setRange(0, samples)

        if self.currentHDFFile == None:
            self.currentHDFFile = h5py.File(filename, "a")

        if path not in self.currentHDFFile:
            self.currentHDFFile.create_dataset(path, (0,), maxshape=(None,), dtype=data.dtype)

        L = len(data)
        EOFFlag = False
        if (L + self.currentHDFFile[path].shape[0]) > samples:
            L = samples - len(self.currentHDFFile[path])
            EOFFlag = True

        current_time = time.time()
        if ((current_time - self.time_record_start) > self.hdf_time_limit_spinBox.value()):
            EOFFlag = True

        self.currentHDFFile[path].resize((self.currentHDFFile[path].shape[0] + L), axis=0)
        self.currentHDFFile[path][-L:] = data[:L]

        self.currentHDFFile.flush()

        self.hdf_recording_progressBar.setValue(self.currentHDFFile[path].shape[0])

        if EOFFlag:
            self.currentHDFFile.close()
            self.currentHDFFile = None
            self.__recording = False
            _logger.info("Done Recording")


    def updateLiveDataTab(self):
        self.plotLiveData()

    def updateSPADTab(self):
        image_H0, bin1,bin2,bin3, dca = processSPADImage(self.currentLiveData_H0)
        if np.sum(image_H0) != 0:
            self.head_0_heatmap.setImage(image_H0, autoLevels=True)
        if np.sum(bin1) != 0:
            self.bin1_heatmap.setImage(bin1, autoLevels=True)
        if np.sum(bin2) != 0:
            self.bin2_heatmap.setImage(bin2, autoLevels=True)
        if np.sum(bin3) != 0:
            self.bin3_heatmap.setImage(bin3, autoLevels=True)
        if np.sum(dca) != 0:
            self.dca_trig_h0_heatmap.setImage(dca, autoLevels=True)

        cr_h0 = processTotalCountRate(self.currentLiveData_H0)

        self.totalCount_H0.display(cr_h0)

        image_H1,_,_,_,_ = processSPADImage(self.currentLiveData_H1)
        if np.sum(image_H1) != 0:
            self.head_1_heatmap.setImage(image_H1, autoLevels=True)

        cr_h1 = processTotalCountRate(self.currentLiveData_H1)
        self.totalCount_H1.display(cr_h1)

        if len(self.currentLiveData_H0['Addr']) != 0:
            self.most_active_spad_h0_lcdNumber.display(stats.mode(self.currentLiveData_H0['Addr']).mode[0])
        if len(self.currentLiveData_H1['Addr']) != 0:
            self.most_active_spad_h1_lcdNumber.display(stats.mode(self.currentLiveData_H1['Addr']).mode[0])


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

        # if status["trigger_divider"]["mux_sel"] == 0:
        #     self.tdc_trig_source_comboBox.setCurrentText("NON_CORR")
        # elif status["trigger_divider"]["mux_sel"] == 1:
        #     self.tdc_trig_source_comboBox.setCurrentText("CORR")
        #
        # if status["window_divider"]["mux_sel"] == 0:
        #     self.wind_trig_source_comboBox.setCurrentText("NON_CORR")
        # elif status["window_divider"]["mux_sel"] == 1:
        #     self.wind_trig_source_comboBox.setCurrentText("CORR")

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
            self.monitorList = ['Timestamp']
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

    def set_DCA_threshold_h0(self, val):
        if val > 0:
            self.board.b.ICYSHSR1.DCA_ENABLE(0,1,0)
        else:
            self.board.b.ICYSHSR1.DCA_ENABLE(0,0,0)
        self.board.b.ICYSHSR1.DCA_THRESHOLD(0, val, 0)



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

        # #array_selected = self.board.b.ICYSHSR1.OUTPUT_MUX_SELECT(0, 0)
        # # a read of OUTPUT_MUX_SELECT will always return 2, because we have to be in read mode to read
        # self.array_select_h0_comboBox.blockSignals(True)
        self.board.b.ICYSHSR1.OUTPUT_MUX_SELECT(0, 0, 0)
        self.array_select_h0_comboBox.setCurrentIndex(0)
        # self.array_select_h0_comboBox.blockSignals(False)
        # #
        # # pp = self.board.b.ICYSHSR1.POST_PROCESSING_SELECT(0, 0)
        # self.post_processing_select_h0_comboBox.blockSignals(True)
        self.board.b.ICYSHSR1.POST_PROCESSING_SELECT(0, 0, 0)
        self.post_processing_select_h0_comboBox.setCurrentIndex(0)
        # self.post_processing_select_h0_comboBox.blockSignals(False)
        # #
        # # trigger_type =  self.board.b.ICYSHSR1.TRIGGER_TYPE(0,0)
        # # if (trigger_type == 0x10):
        # #     trigger_type = 2
        # self.trigger_type_h0_comboBox.blockSignals(True)
        self.board.b.ICYSHSR1.TRIGGER_TYPE(0, 0, 0)
        self.trigger_type_h0_comboBox.setCurrentIndex(0)
        # self.trigger_type_h0_comboBox.blockSignals(False)

        bound_0 = self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_0(0,0)
        self.bound_0_h0_spinBox.setValue(bound_0)
        bound_1 = self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_0_1(0,0)
        self.bound_1_h0_spinBox.setValue(bound_1)
        bound_2 = self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_1_2(0,0)
        self.bound_2_h0_spinBox.setValue(bound_2)
        bound_3 = self.board.b.ICYSHSR1.TIME_BIN_BOUNDS_2(0,0)
        self.bound_3_h0_spinBox.setValue(bound_3)

        pll_enable = (self.board.b.ICYSHSR1.PLL_ENABLE(0,0) == 1)
        self.pll_enable_h0_checkBox.setChecked(pll_enable)

        window_is_stop = (self.board.b.ICYSHSR1.TDC_STOP_SIGNAL(0,0) == 1)
        self.window_is_stop_h0_checkBox.setChecked(window_is_stop)

        window_len = self.board.b.ICYSHSR1.WINDOW(0,0)
        self.window_length_h0_SpinBox.setValue(window_len)


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

        #array = self.array_select_h0_comboBox.currentIndex()
        array = 1
        head  = self.asic_number_h0_spinBox.value()
        freq = 255
        type = self.correction_type_h0_comboBox.currentText()

        #skew_filename = 'H7_M1_1v278_skew.pickle'
        skew_filename = "H{0}_M{1}_skew.pickle".format(int(head), int(array), int(freq), type)

        #skew_filename = 'H8_M1_1v27_skew.pickle'

        with open(skew_filename, 'rb') as f:
            skew_corr = pickle.load(f)
            for tdc in range(len(skew_corr)):
                self.board.asic_head_0.set_skew_correction(array, tdc*4, int(skew_corr[tdc]))


        corr_filename = "H{0}_M{1}_{3}.pickle".format(int(head), int(array), int(freq), type)

        #corr_filename = "19oct_corr_coef_lin_bias_slope.pickle"
        #corr_filename = "H8_M1_1v27_lin_bias_slope.pickle"


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


    def runCalibSequence(self):

        isAverageCoarse8 = False
        while (isAverageCoarse8 != True):

            cur_slow_freq  = self.dac_slow_h0_SpinBox.value()

            filename = "CoarseAdj.hdf5"
            path = "CoarseAdj"
            groupName = path
            datasetPath = path + "/RAW"

            self.hdf_filename_lineEdit.setText(filename)
            self.hdf_path_lineEdit.setText(datasetPath)
            self.hdf_samples_spinBox.setValue(1000000)

            time.sleep(2)
            self.__recording = True
            while (self.__recording):
                time.sleep(1)


            time.sleep(1)

            avgCoarse = calcMaxCoarse(filename, path)
            if (avgCoarse > 7.9) and (avgCoarse < 8.1):
                isAverageCoarse8 = True
            elif (avgCoarse <= 7.9):
                cur_slow_freq += 0.001
                #self.board.v_slow_head_0.set_voltage(cur_slow_freq)
                self.dac_slow_h0_SpinBox.setValue(cur_slow_freq)
                _logger.info("Average coarse was: " + str(avgCoarse) + ", setting slow to: " + str(cur_slow_freq))
            elif (avgCoarse >= 8.1):
                cur_slow_freq -= 0.001
                #self.board.v_slow_head_0.set_voltage(cur_slow_freq)
                self.dac_slow_h0_SpinBox.setValue(cur_slow_freq)
                _logger.info("Average coarse was: " + str(avgCoarse) + ", setting slow to: " + str(cur_slow_freq))

            os.remove(filename)

        _logger.info(" === Done Coarse adjustment step ===")

        # find fast that gives an average of 50 fine
        _logger.info(" === Starting Fine adjustment step ===")
        isAverageFine50 = False
        while (isAverageFine50 == False):

            cur_fast_freq  = self.dac_fast_h0_SpinBox.value()


            filename = "FineAdj.hdf5"
            path = "FineAdj"
            groupName = path
            datasetPath = path + "/RAW"

            self.hdf_filename_lineEdit.setText(filename)
            self.hdf_path_lineEdit.setText(datasetPath)
            self.hdf_samples_spinBox.setValue(1000000)

            time.sleep(2)
            self.__recording = True
            while (self.__recording):
                time.sleep(1)

            time.sleep(1)
            avgFine = calcMaxFine(self.filename, path)
            if (avgFine > 45) and (avgFine < 55):
                isAverageCoarse8 = True
            elif (avgFine <= 45):
                cur_fast_freq -= 0.001
                #self.board.v_fast_head_0.set_voltage(cur_fast_freq)
                self.dac_fast_h0_SpinBox.setValue(cur_fast_freq)
                _logger.info("Average fine was: " + str(avgFine) + ", setting fast to: " + str(cur_fast_freq))
                os.remove(filename)
            elif (avgFine >= 55):
                cur_fast_freq += 0.001
                #self.board.v_fast_head_0.set_voltage(cur_fast_freq)
                self.dac_fast_h0_SpinBox.setValue(cur_fast_freq)
                _logger.info("Average fine was: " + str(avgFine) + ", setting fast to: " + str(cur_fast_freq))
                os.remove(filename)

        _logger.info(" === Done Fine adjustment step ===")

