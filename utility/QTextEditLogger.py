import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor
import logging


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = parent
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        if record.levelname == 'INFO':
            self.widget.setTextColor(QColor(0,0,0))
        elif record.levelname == 'WARNING':
            self.widget.setTextColor(QColor(255,128,0))
        elif record.levelname == 'ERROR':
            self.widget.setTextColor(QColor(255,0,0))
        elif record.levelname == 'CRITICAL':
            self.widget.setTextColor(QColor(255,0,0))
        elif record.levelname == 'DEBUG':
            self.widget.setTextColor(QColor(0,0,255))
        self.widget.append(msg)