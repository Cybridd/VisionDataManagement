"""
Created on 8/10/2018 18:59

Subclasses of Qt's QObject hierarchy. ClickLabel adds on-click signals and an
index attribute to QLabel, and VideoPlayer uses a QTimer and OpenCV to update
observing UI elements (QLabels) with a 30fps video stream.

@author: Connor Fulton
"""

from PyQt5 import QtWidgets, QtCore
from QtWidgets import *
from QtCore import pyqtSignal, QTimer
from model import Video
import time
import processing as ip
import cv2

class ClickLabel(QLabel):
    """Adds on-click functionality to Qt's QLabel"""
    clicked=pyqtSignal(int)
    unhighlighted=pyqtSignal(int)

    def __init__(self, parent=None, index=0):
        QLabel.__init__(self, parent)
        self.index = index
        self.highlighted = False

    def mousePressEvent(self, event):
        self.highlighted = not self.highlighted
        if self.highlighted:
            self.makeHighlighted()
            self.clicked.emit(self.index)
        else:
            self.notHighlighted()
            self.unhighlighted.emit(self.index)

    def setIndex(self, index):
        self.index = index

    def makeHighlighted(self):
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setLineWidth(3)

    def notHighlighted(self):
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setLineWidth(1)

class VideoPlayer(QWidget):
    """Enables playback functions and broadcasting of video stream to UI elements

    Subscribers are named individually because they require different images or data
    """

    video = None
    videoFrame = None
    focalFrame = None
    corticalFrame = None
    focusFrame = None
    framePos = 0
    maxFrames = 0
    retina = None
    cortex = None
    fixation = None
    filetypes = {
        'mp4': 'mp4v',
        'jpg': 'jpeg',
        'avi': 'xvid'
    }

    def __init__(self,file,isRetinaEnabled,parent,webcammode=False):
        super(QWidget,self).__init__()
        self.parent = parent
        self.isVideo = False
        self.webcam = webcammode
        if file:
            self.file = file
            self.isVideo = isinstance(file,Video)
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrame)
        self.frames = parent.currentFrames
        # set up video capture dependent on source
        if self.isVideo:
            self.cap = cv2.VideoCapture(self.file.filepath)
            codec = cv2.VideoWriter_fourcc(*self.filetypes[self.file.type])
            self.cap.set(cv2.CAP_PROP_FOURCC, codec)
            self.maxFrames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        # if webcam mode, start immediately
        elif self.webcam:
            self.cap = cv2.VideoCapture(0)
            self.isBGR = True
            self.timer.start(1000.0/30)
        # if still images, no need for video capture
        else:
            self.maxFrames = len(self.frames) - 1
        self.parent.scrubSlider.setRange(0,self.maxFrames)
        self.parent.scrubSlider_2.setRange(0,self.maxFrames)
        self.framePos = 0
        self.videoFrame = parent.label
        self.focalFrame = parent.focallabel
        self.corticalFrame = parent.corticallabel
        self.focusFrame = parent.biglabel
        if isRetinaEnabled:
            self.retina, self.fixation = ip.prepareLiveRetina(self.cap)
            self.cortex = ip.createCortex()


    def nextFrame(self):
        """Retrieves next frame for display whether video or image"""
        if self.isVideo or self.webcam:
            ret, frame = self.cap.read()
            if ret:
                self.framePos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                self.updateDisplay(frame)
        else:
            self.framePos += 1 if self.framePos < self.maxFrames else 0
            self.setCurrent()

    def start(self):
        self.timer.start(1000.0/30)
        self.parent.startButton.setDisabled(True)
        self.parent.startButton_2.setDisabled(True)
        self.parent.pauseButton.setDisabled(False)
        self.parent.pauseButton_2.setDisabled(False)

    def pause(self):
        self.timer.stop()
        self.parent.pauseButton.setDisabled(True)
        self.parent.pauseButton_2.setDisabled(True)
        self.parent.startButton.setDisabled(False)
        self.parent.startButton_2.setDisabled(False)

    def setCurrent(self):
        """Sets the current frame based on user input from playback buttons"""
        if self.framePos <= self.maxFrames:
            if self.isVideo:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.framePos)
            else:
                self.currentframe = self.frames[self.framePos]
                self.updateDisplay(self.currentframe.image)

    def skip(self, framePos):
        self.framePos = framePos
        self.setCurrent()

    def skipBck(self):
        self.framePos = self.framePos - 1 if self.framePos > 0 else 0
        self.setCurrent()

    def skipFwd(self):
        self.framePos = self.framePos + 1 if self.framePos < self.maxFrames else 0
        self.setCurrent()

    def updateDisplay(self, frame):
        """Update all subscribed UI elements with images or data"""
        self.parent.scrubSlider.setValue(self.framePos)
        self.parent.scrubSlider_2.setValue(self.framePos)
        self.parent.frameNum.display(self.framePos)
        self.parent.frameNum_2.display(self.framePos)
        # update the metadata table if we're on the main tab
        if self.parent.maintabWidget.currentIndex() == 1:
            self.parent.displayMetaData(self.framePos)
        if not (self.isVideo or self.webcam):
            self.isBGR = self.currentframe.vectortype == 'BGR'
        self.videoFrame.setPixmap(ip.convertToPixmap(frame, 480, 360, self.isBGR))
        # if retina is activated display live backprojection and cortical image
        if self.retina:
            v = self.retina.sample(frame,self.fixation)
            tight = self.retina.backproject_last()
            cortical = self.cortex.cort_img(v)
            self.focalFrame.setPixmap(ip.convertToPixmap(tight, 480, 360, self.isBGR))
            self.corticalFrame.setPixmap(ip.convertToPixmap(cortical, 480, 360, self.isBGR))
            self.focusFrame.setPixmap(ip.convertToPixmap(cortical, 1280, 720, self.isBGR))
        else:
            self.focusFrame.setPixmap(ip.convertToPixmap(frame, 1280, 720, self.isBGR))
