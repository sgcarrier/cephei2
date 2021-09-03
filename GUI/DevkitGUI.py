from pyqtgraph.Qt import QtCore, QtGui
from PyQt5 import QtWidgets, uic
from GUI.DevkitControl import DevkitControl
from GUI.DevkitView import DevkitView
import time
import logging


_logger = logging.getLogger(__name__)

class DevkitGUI():
    def __init__(self):

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root.addHandler(handler)

        self.__controller = DevkitControl()

        try:
            self.__viewer = DevkitView()
        except Exception as e:
            _logger.critical("Could not create viewer due to raised exception: " +  str(e))
            exit(1)




    def start(self):
        _logger.info("Starting the GUI")
        #self.__controller.connect()
        self.__viewer.connect()

        time.sleep(0.5)

        timer = QtCore.QTimer(self.__viewer)
        timer.timeout.connect(self.__viewer.update)
        timer.start(10)

        time.sleep(0.5)

        self.__viewer.show()



if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)

    GUI = DevkitGUI()

    GUI.start()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()