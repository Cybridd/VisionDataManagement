from PyQt5 import QtWidgets, QtCore
from QtWidgets import QLabel
from QtCore import pyqtSignal

class ClickLabel(QLabel):
    clicked=pyqtSignal(int)

    def __init__(self, parent=None, index=0):
        QLabel.__init__(self, parent)
        self.index = index

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)

    def setIndex(self, index):
        self.index = index
