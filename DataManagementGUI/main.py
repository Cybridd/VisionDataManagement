from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import design
import numpy as np
import cv2
import threading
import time
from QtCore import QThread, pyqtSignal, Qt
from QtGui import QImage, QPixmap
from QtWidgets import QMainWindow, QInputDialog, QFileDialog

class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            rgbImage = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            converttoQtFormat = QImage(rgbImage.data,rgbImage.shape[1],rgbImage.shape[0],QImage.Format_RGB888)
            pic = converttoQtFormat.scaled(640,480,Qt.KeepAspectRatio)
            self.changePixmap.emit(pic)

class DMApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self,parent=None):
        super(DMApp,self).__init__(parent)
        self.setupUi(self)
        self.webcamButton.clicked.connect(self.startWebCam)
        self.browseButton.clicked.connect(self.openFileNameDialog)

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            print(fileName)

    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            print(fileName)

    def startWebCam(self, event):
        vidThread = Thread(self)
        vidThread.changePixmap.connect(self.setImage)
        vidThread.start()

    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

def main():
    app = QtWidgets.QApplication(sys.argv)
    form = DMApp()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
