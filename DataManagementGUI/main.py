from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os
import design
import ImageProcessing
import numpy as np
import csv
import cv2
import threading
import time
import qtmodern
from os.path import join
from retinavision.retina import Retina
from retinavision.cortex import Cortex
from retinavision import utils
from model import Image as im, Video as vid
from QtCore import QThread, pyqtSignal, Qt, QTimer
from QtGui import QImage, QPixmap, QStandardItem
from QtWidgets import QApplication, QMainWindow, QInputDialog, QFileDialog, QWidget, QMessageBox
from qtmodern import styles, windows

#TODO metadata editing, deleting files, ImageProcessing class, export for DCNN

class VideoPlayer(QWidget):

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    videoName = None
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

    def __init__(self,fileName,fileType,isRetinaEnabled,parent):
        super(QWidget,self).__init__()
        self.videoName = fileName
        print(self.videoName)
        self.parent = parent
        if self.videoName:
            self.cap = cv2.VideoCapture(self.videoName)
            self.setCodec(fileType)
            self.maxFrames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            self.parent.scrubSlider.setRange(0,self.maxFrames)
        else:
            self.cap = cv2.VideoCapture(0)
        self.videoFrame = parent.label
        self.focalFrame = parent.focallabel
        self.corticalFrame = parent.corticallabel
        self.focusFrame = parent.biglabel
        if isRetinaEnabled:
            print("Retina enabled signal received")
            self.retina, self.fixation = ImageProcessing.startRetina(self.cap)
            self.cortex = ImageProcessing.createCortex()

    def setCodec(self,filetype):
        codec = cv2.VideoWriter_fourcc(*self.filetypes[filetype])
        self.cap.set(cv2.CAP_PROP_FOURCC, codec)

    def nextFrame(self):
        ret, frame = self.cap.read()
        if ret:
            framePos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            self.videoFrame.setPixmap(self.convertToPixmap(frame, 480, 360))
            if self.retina:
                v = self.retina.sample(frame,self.fixation)
                tight = self.retina.backproject_last()
                cortical = self.cortex.cort_img(v)
                self.focalFrame.setPixmap(self.convertToPixmap(tight, 480, 360))
                self.corticalFrame.setPixmap(self.convertToPixmap(cortical, 480, 360))
                self.focusFrame.setPixmap(self.convertToPixmap(cortical, 1280, 720))
            else:
                self.focusFrame.setPixmap(self.convertToPixmap(frame, 1280, 720))
            self.parent.scrubSlider.setValue(framePos)
            self.parent.frameNum.display(framePos)

    def convertToPixmap(self, frame, x, y):
        rgbImage = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        converttoQtFormat = QImage(rgbImage.data,rgbImage.shape[1],rgbImage.shape[0],QImage.Format_RGB888)
        pic = converttoQtFormat.scaled(x,y,Qt.KeepAspectRatio)
        pixmap = QPixmap.fromImage(pic)
        return pixmap

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
        self.parent.frameNum.display(framePos)

class DMApp(QMainWindow, design.Ui_MainWindow):

    fileName = None
    datadir = None
    currentFile = None
    metaFileName = None
    metadatamodel = None
    fileType = None
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
        self.browseFolderButton.clicked.connect(self.openFolderDialog)
        self.retinaButton.clicked[bool].connect(self.setRetinaEnabled)
        self.maintabWidget.setCurrentIndex(0)

    def openFileNameDialog(self):
        mediafiletypes = {'mp4','avi','jpg'}
        metadatatypes = {'csv','json'}
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open file", "",
            "All Files (*);;mp4 Files (*.mp4);;avi Files (*.avi);;jpeg Files (*.jpg);;csv Files (*.csv);;json Files(*.json)",
            options=options)
        filetype = fileName.split('.')[-1]
        if fileName:
            print("Opening " + fileName)
            if filetype in mediafiletypes:
                self.currentFile = vid.Video(filepath=fileName,palette="rgb")
                #self.fileName = fileName
                #self.fileType = filetype
                #self.startVideoPlayer()
            elif filetype in metadatatypes:
                self.metaFileName = fileName
                self.fileType = filetype
                self.loadMetaData()
            else:
                self.showWarning('filetype')

    def openFolderDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        datadir = QFileDialog.getExistingDirectory(self, "Open folder")
        if datadir:
            print("Directory opened:" + datadir)

    def loadMetaData(self):
        self.metadatamodel = QtGui.QStandardItemModel(self)
        file = open(self.metaFileName,'rb')
        reader = csv.reader(file)
        #self.metadata.clear()
        for row in reader:
            items = [
                QStandardItem(field)
                for field in row
            ]
            self.metadatamodel.appendRow(items)
        self.metadata.setModel(self.metadatamodel)


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
        #if not self.videoPlayer and self.isVideoLoaded:
        self.videoPlayer = VideoPlayer(self.fileName,self.fileType,self.isRetinaEnabled, self)
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
            self.browseFolderButton.setDisabled(True)
            self.scrubSlider.setDisabled(True)
        else:
            self.videoPlayer = None
            self.browseButton.setDisabled(False)

    def getGalleryWidgets(self):
        labels = self.dataframe_2.findChildren(QLabel)

    def showWarning(self, error):
        errormessage = QMessageBox()
        errormessage.setStandardButtons(QMessageBox.Ok)
        errormessage.setWindowTitle('Warning')
        errormessage.setIcon(QMessageBox.Warning)
        if error == 'filetype':
            errormessage.setText("File type not supported")
        errormessage.exec_()


def main():
    app = QApplication(sys.argv)
    form = DMApp()
    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(form)
    mw.show()
    app.exec_()

if __name__ == '__main__':
    main()
