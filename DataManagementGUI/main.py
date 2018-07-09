from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os
import design
import numpy as np
import cv2
import threading
import time
import qtmodern
from QtCore import QThread, pyqtSignal, Qt
from QtGui import QImage, QPixmap
from QtWidgets import QApplication, QMainWindow, QInputDialog, QFileDialog
from qtmodern import styles, windows

class Thread(QThread):

    changePixmap = pyqtSignal(QImage)
    videoName = None
    def __init__(self,fileName,parent=None):
        super(Thread,self).__init__()
        self.videoName = fileName

    def run(self):
        if self.videoName:
            cap = cv2.VideoCapture(self.videoName)
            codec = cv2.VideoWriter_fourcc(*'mp4v')
            cap.set(cv2.CAP_PROP_FOURCC, codec)
        else:
            cap = cv2.VideoCapture(0)
        cv2.waitKey(0)
        while not QThread.currentThread().isInterruptionRequested():
            ret, frame = cap.read()
            rgbImage = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            converttoQtFormat = QImage(rgbImage.data,rgbImage.shape[1],rgbImage.shape[0],QImage.Format_RGB888)
            pic = converttoQtFormat.scaled(640,480,Qt.KeepAspectRatio)
            self.changePixmap.emit(pic)
        cap.release()


class DMApp(QMainWindow, design.Ui_MainWindow):

    vidThread = None
    fileName = None

    def __init__(self,parent=None):
        super(DMApp,self).__init__(parent)
        self.setupUi(self)
        self.webcamButton.clicked[bool].connect(self.runWebCam)
        self.browseButton.clicked.connect(self.openFileNameDialog)

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open file", "","All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            print("Opening " + fileName)
            self.runThread(fileName)

    #Not currently in use
    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.fileName, _ = QFileDialog.getSaveFileName(self,"Save file","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            print(fileName)

    def runThread(self, fileName):
        self.vidThread = Thread(fileName)
        self.vidThread.changePixmap.connect(self.setImage)
        self.vidThread.start()

    def runWebCam(self, event):
        if event:
            self.runThread(None)
            self.browseButton.setDisabled(True)
        else:
            self.vidThread.requestInterruption()
            self.browseButton.setDisabled(False)

    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

def main():
    app = QApplication(sys.argv)
    form = DMApp()
    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(form)
    mw.show()
    app.exec_()

if __name__ == '__main__':
    main()
