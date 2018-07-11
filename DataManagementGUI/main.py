from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os
import design
import numpy as np
import cv2
import threading
import time
import qtmodern
from os.path import join
from retinavision.retina import Retina
from retinavision.cortex import Cortex
from retinavision import datadir, utils
from QtCore import QThread, pyqtSignal, Qt, QTimer
from QtGui import QImage, QPixmap
from QtWidgets import QApplication, QMainWindow, QInputDialog, QFileDialog, QWidget
from qtmodern import styles, windows

#TODO multi-frame display, metadata editing,
# add retina instance for webcam, VideoPreProcessing class, export for DCNN
class VideoPlayer(QWidget):

    videoName = None
    videoFrame = None
    focalFrame = None
    corticalFrame = None
    framePos = 0
    maxFrames = 0
    retina = None
    cortex = None


    def __init__(self,fileName,isRetinaEnabled,parent):
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
        self.focalFrame = parent.focallabel
        self.corticalFrame = parent.corticallabel
        if isRetinaEnabled:
            print("Retina enabled signal received")
            self.startRetina()
            self.createCortex()

    def nextFrame(self):
        ret, frame = self.cap.read()
        if ret:
            framePos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            self.videoFrame.setPixmap(self.convertToPixmap(frame))
            if self.retina:
                v = self.retina.sample(frame,self.fixation)
                tight = self.retina.backproject_last()
                cortical = self.cortex.cort_img(v)
                self.focalFrame.setPixmap(self.convertToPixmap(tight))
                self.corticalFrame.setPixmap(self.convertToPixmap(cortical))
            #self.parent.scrubSlider.setValue(framePos)
            self.parent.frameNum.display(framePos)

    def convertToPixmap(self, frame):
        rgbImage = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        converttoQtFormat = QImage(rgbImage.data,rgbImage.shape[1],rgbImage.shape[0],QImage.Format_RGB888)
        pic = converttoQtFormat.scaled(480,360,Qt.KeepAspectRatio)
        pixmap = QPixmap.fromImage(pic)
        return pixmap

    def startRetina(self):
        if not self.retina and self.cap:
            ret, frame = self.cap.read()
            self.retina = Retina()
            self.retina.loadLoc(join(datadir, "retinas", "ret50k_loc.pkl"))
            self.retina.loadCoeff(join(datadir, "retinas", "ret50k_coeff.pkl"))
            x = frame.shape[1]/2
            y = frame.shape[0]/2
            self.fixation = (y,x)
            self.retina.prepare(frame.shape, self.fixation)

    def createCortex(self):
        if not self.cortex:
            self.cortex = Cortex()
            lp = join(datadir, "cortices", "Ll.pkl")
            rp = join(datadir, "cortices", "Rl.pkl")
            self.cortex.loadLocs(lp, rp)
            self.cortex.loadCoeffs(join(datadir, "cortices", "Lcoeff.pkl"), join(datadir, "cortices", "Rcoeff.pkl"))

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

    fileName = None
    timer = None
    posFile = None
    videoPlayer = None
    isRetinaEnabled = False
    #isPosFileLoaded = False
    #isVideoLoaded = False

    def __init__(self,parent=None):
        super(DMApp,self).__init__(parent)
        self.setupUi(self)
        self.webcamButton.clicked[bool].connect(self.runWebCam)
        self.browseButton.clicked.connect(self.openFileNameDialog)
        self.retinaButton.clicked[bool].connect(self.setRetinaEnabled)

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

    def setRetinaEnabled(self, event):
        if event:
            self.isRetinaEnabled = True
        else:
            self.isRetinaEnabled = False

    def startVideoPlayer(self):
        if not self.videoPlayer:# and self.isVideoLoaded:
            self.videoPlayer = VideoPlayer(self.fileName, self.isRetinaEnabled, self)
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
