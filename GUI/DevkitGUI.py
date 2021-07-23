from pyqtgraph.Qt import QtCore, QtGui
from PyQt5 import QtWidgets, uic
from GUI.DevkitControl import DevkitControl
from GUI.DevkitView import DevkitView
import time


class DevkitGUI():
    def __init__(self):
        self.__controller = DevkitControl()
        self.__viewer = DevkitView()

    def start(self):

        self.__controller.connect()
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