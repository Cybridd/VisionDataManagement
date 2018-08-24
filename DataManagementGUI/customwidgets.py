from PyQt5 import QtWidgets, QtCore
from QtWidgets import *
from QtCore import pyqtSignal, QTimer
from model import Video
import time
import processing as ip
import cv2

class ClickLabel(QLabel):

    clicked=pyqtSignal(int)
    unhighlighted=pyqtSignal(int)

    def __init__(self, parent=None, index=0):
        QLabel.__init__(self, parent)
        self.index = index
        self.highlighted = False

    def mousePressEvent(self, event):
        #self.clicked.emit(self.index)
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
            self.isVideo = isinstance(file,Video) # self.file.split(".")[-1] in self.filetypes.keys()
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrame)
        self.frames = parent.currentFrames
        if self.isVideo:
            self.cap = cv2.VideoCapture(self.file.filepath)
            codec = cv2.VideoWriter_fourcc(*self.filetypes[self.file.type])
            self.cap.set(cv2.CAP_PROP_FOURCC, codec)
            self.maxFrames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            self.parent.scrubSlider.setRange(0,self.maxFrames)
        elif self.webcam:
            self.cap = cv2.VideoCapture(0)
            self.timer.start(1000.0/30)
        else:
            self.maxFrames = len(self.frames) - 1
        self.framePos = 0
        self.videoFrame = parent.label
        self.focalFrame = parent.focallabel
        self.corticalFrame = parent.corticallabel
        self.focusFrame = parent.biglabel
        if isRetinaEnabled:
            self.retina, self.fixation = ip.prepareLiveRetina(self.cap)
            self.cortex = ip.createCortex()


    def nextFrame(self):
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
        if self.framePos <= self.maxFrames:
            if self.isVideo:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.framePos)
            else:
                currentframe = self.frames[self.framePos]
                self.updateDisplay(currentframe.image)

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
        print("update display called")
        self.parent.scrubSlider.setValue(self.framePos)
        self.parent.scrubSlider_2.setValue(self.framePos)
        self.parent.frameNum.display(self.framePos)
        self.parent.frameNum_2.display(self.framePos)
        self.parent.displayMetaData(self.framePos)
        self.videoFrame.setPixmap(ip.convertToPixmap(frame, 480, 360))
        if self.retina:
            start = time.time()
            v = self.retina.sample(frame,self.fixation)
            print(frame.shape)
            tight = self.retina.backproject_last()
            end = time.time()
            print("Frame took " + str(end - start) + " seconds.")
            cortical = self.cortex.cort_img(v)
            self.focalFrame.setPixmap(ip.convertToPixmap(tight, 480, 360))
            self.corticalFrame.setPixmap(ip.convertToPixmap(cortical, 480, 360))
            self.focusFrame.setPixmap(ip.convertToPixmap(cortical, 1280, 720))
        else:
            self.focusFrame.setPixmap(ip.convertToPixmap(frame, 1280, 720))
