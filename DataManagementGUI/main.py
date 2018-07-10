from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os
import design
import numpy as np
import cv2
import threading
import time
import qtmodern
from QtCore import QThread, pyqtSignal, Qt, QTimer
from QtGui import QImage, QPixmap
from QtWidgets import QApplication, QMainWindow, QInputDialog, QFileDialog, QWidget
from qtmodern import styles, windows

#class Thread(QThread):
#
#    changePixmap = pyqtSignal(QImage)
#    videoName = None
#    def __init__(self,fileName,parent=None):
#        super(Thread,self).__init__()
#        self.videoName = fileName
#
#    def run(self):
#        if self.videoName:
#            cap = cv2.VideoCapture(self.videoName)
#            codec = cv2.VideoWriter_fourcc(*'mp4v')
#            cap.set(cv2.CAP_PROP_FOURCC, codec)
#        else:
#            cap = cv2.VideoCapture(0)
#        cv2.waitKey(0)
#        while not QThread.currentThread().isInterruptionRequested():
#            ret, frame = cap.read()
#            rgbImage = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
#            converttoQtFormat = QImage(rgbImage.data,rgbImage.shape[1],rgbImage.shape[0],QImage.Format_RGB888)
#            pic = converttoQtFormat.scaled(640,480,Qt.KeepAspectRatio)
#            self.changePixmap.emit(pic)
#        cap.release()

class VideoPlayer(QWidget):

    changePixmap = pyqtSignal(QImage)
    videoName = None
    videoFrame = None

    def __init__(self,fileName,parent):
        super(QWidget,self).__init__()
        self.videoName = fileName
        if self.videoName:
            self.cap = cv2.VideoCapture(self.videoName)
            codec = cv2.VideoWriter_fourcc(*'mp4v')
            self.cap.set(cv2.CAP_PROP_FOURCC, codec)
        else:
            self.cap = cv2.VideoCapture(0)
        self.videoFrame = parent.label

    def nextFrame(self):
        ret, frame = self.cap.read()
        rgbImage = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        converttoQtFormat = QImage(rgbImage.data,rgbImage.shape[1],rgbImage.shape[0],QImage.Format_RGB888)
        pic = converttoQtFormat.scaled(640,480,Qt.KeepAspectRatio)
        #self.changePixmap.emit(pic)
        self.videoFrame.setPixmap(QPixmap.fromImage(pic))

        #setPixmap done in setImage of DMApp class - move it here?

    def start(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrame)
        self.timer.start(1000.0/30)

    def pause(self, event):
        if event:
            self.timer.stop()
        else:
            self.timer.start()

class DMApp(QMainWindow, design.Ui_MainWindow):

    vidThread = None
    fileName = None
    timer = None
    posFile = None
    videoPlayer = None
    isPosFileLoaded = False
    isVideoLoaded = False

    def __init__(self,parent=None):
        super(DMApp,self).__init__(parent)
        self.setupUi(self)
        self.webcamButton.clicked[bool].connect(self.runWebCam)
        self.browseButton.clicked.connect(self.openFileNameDialog)
        #self.pauseButton.clicked[bool].connect(self.videoPlayer.pause)
        #self.startVideoPlayer()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open file", "","All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            print("Opening " + fileName)
            self.fileName = fileName
            self.startVideoPlayer()

    #Not currently in use
    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.fileName, _ = QFileDialog.getSaveFileName(self,"Save file","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            print(fileName)

#    def runThread(self, fileName):
#        self.vidThread = Thread(fileName)
#        self.vidThread.changePixmap.connect(self.setImage)
#        self.timer = QTimer()
#        self.timer.moveToThread(self.vidThread)
#        self.vidThread.start()

    def startVideoPlayer(self):
        if not self.videoPlayer:# and self.isVideoLoaded:
            self.videoPlayer = VideoPlayer(self.fileName, self)
            self.pauseButton.clicked[bool].connect(self.videoPlayer.pause)
        self.videoPlayer.start()

    def runWebCam(self, event):
        if event:
            #self.runThread(None)
            self.fileName = 0
            self.isVideoLoaded = True
            self.startVideoPlayer()
            self.browseButton.setDisabled(True)
        else:
            self.videoPlayer = None
            #self.videoPlayer.pause(event)
            self.browseButton.setDisabled(False)

#    def setImage(self, image):
#        self.label.setPixmap(QPixmap.fromImage(image))

#    def pause(self, event):
#        if event:
#            self.timer.stop()
#        else:
#            self.timer.start()

def main():
    app = QApplication(sys.argv)
    form = DMApp()
    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(form)
    mw.show()
    app.exec_()

if __name__ == '__main__':
    main()
