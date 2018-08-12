from PyQt5 import QtWidgets, QtCore
from QtWidgets import QLabel
from QtCore import pyqtSignal

class ClickLabel(QLabel):
    clicked=pyqtSignal(int)

    def __init__(self, parent=None, index=0):
        QLabel.__init__(self, parent)
        self.index = index
        self.highlighted = False

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)
        self.highlighted = not self.highlighted
        if self.highlighted:
            self.setFrameShape(QtWidgets.QFrame.Box)
            self.setLineWidth(3)
        else:
            self.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.setLineWidth(1)

    def setIndex(self, index):
        self.index = index
