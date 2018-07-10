from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os
import design
import numpy as np
import cv2
import threading
import time
import qtmodern
from retinavision.retina import Retina
from retinavision.cortex import Cortex
from retinavision import datadir, utils
from QtCore import QThread, pyqtSignal, Qt, QTimer
from QtGui import QImage, QPixmap
from QtWidgets import QApplication, QMainWindow, QInputDialog, QFileDialog, QWidget
from qtmodern import styles, windows

class VideoPlayer(QWidget):

    videoName = None
    videoFrame = None
    framePos = 0
    maxFrames = 0

    def __init__(self,fileName,parent):
        super(QWidget,self).__init__()
        self.videoName = fileName
        self.parent = parent
        if self.videoName:
            self.cap = cv2.VideoCapture(self.videoName)
            codec = cv2.VideoWriter_fourcc(*'mp4v')
            self.cap.set(cv2.CAP_PROP_FOURCC, codec)
            self.maxFrames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            self.parent.scrubSlider.maximum = self.maxFrames
        else:
            self.cap = cv2.VideoCapture(0)
        self.videoFrame = parent.label

    def nextFrame(self):
        ret, frame = self.cap.read()
        if ret:
            framePos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            rgbImage = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            converttoQtFormat = QImage(rgbImage.data,rgbImage.shape[1],rgbImage.shape[0],QImage.Format_RGB888)
            pic = converttoQtFormat.scaled(480,360,Qt.KeepAspectRatio)
            self.videoFrame.setPixmap(QPixmap.fromImage(pic))
            self.parent.scrubSlider.setValue(framePos)
            self.parent.frameNum.display(framePos)

    def start(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrame)
        self.timer.start(1000.0/30)

    def pause(self, event):
        if event:
            self.timer.stop()
        else:
            self.timer.start()

    def skip(self, framePos):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, framePos)
        self.parent.scrubSlider.setValue(framePos)
        self.parent.frameNum.display(framePos)

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

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open file", "","All Files (*);;mp4 Files (*.mp4)", options=options)
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

    def startVideoPlayer(self):
        if not self.videoPlayer:# and self.isVideoLoaded:
            self.videoPlayer = VideoPlayer(self.fileName, self)
            self.pauseButton.clicked[bool].connect(self.videoPlayer.pause)
            self.scrubSlider.valueChanged.connect(self.sendFramePos)
        self.videoPlayer.start()

    def sendFramePos(self):
        framePos = self.scrubSlider.value()
        self.videoPlayer.skip(framePos)

    def runWebCam(self, event):
        if event:
            self.fileName = 0
            self.isVideoLoaded = True
            self.startVideoPlayer()
            self.browseButton.setDisabled(True)
            self.scrubSlider.setDisabled(True)
        else:
            self.videoPlayer = None
            self.browseButton.setDisabled(False)

def main():
    app = QApplication(sys.argv)
    form = DMApp()
    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(form)
    mw.show()
    app.exec_()

if __name__ == '__main__':
    main()
