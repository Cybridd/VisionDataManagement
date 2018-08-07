import sys, traceback
import os
import design
import cv2
import time
import numpy as np
import h5py
import ImageProcessing
from os.path import join
from model import Image, ImageVector, Video
from worker import Worker
from retinavision import utils
from PyQt5 import QtCore, QtGui, QtWidgets
from QtCore import *
from QtGui import *
from QtWidgets import *

#TODO metadata editing, deleting files, export for DCNN,
# Give to Worker - Image/Video object creation, image saving/exporting, display updating

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

    def __init__(self,video,isRetinaEnabled,parent):
        super(QWidget,self).__init__()
        self.parent = parent
        self.video = video
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrame)
        if self.video:
            self.cap = cv2.VideoCapture(self.video.filepath)
            codec = cv2.VideoWriter_fourcc(*self.filetypes[self.video.type])
            self.cap.set(cv2.CAP_PROP_FOURCC, codec)
            self.maxFrames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            self.parent.scrubSlider.setRange(0,self.maxFrames)
        else:
            self.cap = cv2.VideoCapture(0)
            self.timer.start(1000.0/30)
        self.videoFrame = parent.label
        self.focalFrame = parent.focallabel
        self.corticalFrame = parent.corticallabel
        self.focusFrame = parent.biglabel
        if isRetinaEnabled:
            print("Retina enabled signal received")
            self.retina, self.fixation = ImageProcessing.startRetina(self.cap)
            self.cortex = ImageProcessing.createCortex()


    def nextFrame(self):
        ret, frame = self.cap.read()
        if ret:
            self.framePos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            self.updateDisplay(frame)

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

    def skip(self, framePos):
        self.framePos = framePos
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.framePos)
        #self.updateDisplay()

    def skipBck(self):
        self.framePos = self.framePos - 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.framePos)
        #self.updateDisplay()

    def skipFwd(self):
        self.framePos = self.framePos + 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.framePos)
        #self.updateDisplay()

    def updateDisplay(self, frame):
        self.parent.scrubSlider.setValue(self.framePos)
        self.parent.scrubSlider_2.setValue(self.framePos)
        self.parent.frameNum.display(self.framePos)
        self.parent.frameNum_2.display(self.framePos)
        self.videoFrame.setPixmap(ImageProcessing.convertToPixmap(frame, 480, 360))
        if self.retina:
            v = self.retina.sample(frame,self.fixation)
            tight = self.retina.backproject_last()
            cortical = self.cortex.cort_img(v)
            self.focalFrame.setPixmap(ImageProcessing.convertToPixmap(tight, 480, 360))
            self.corticalFrame.setPixmap(ImageProcessing.convertToPixmap(cortical, 480, 360))
            self.focusFrame.setPixmap(ImageProcessing.convertToPixmap(cortical, 1280, 720))
        else:
            self.focusFrame.setPixmap(ImageProcessing.convertToPixmap(frame, 1280, 720))

class DMApp(QMainWindow, design.Ui_MainWindow):

    #ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    fileName = None
    currentDir = None
    currentFile = None
    currentFrames = None
    metaFileName = None
    metadatamodel = None
    fileType = None
    posFile = None
    videoPlayer = None
    isRetinaEnabled = False
    videofiletypes = {'mp4','avi'}
    metadatatypes = {'csv','json'}
    rawvectortypes = {'npy','npz'}

    def __init__(self,parent=None):
        super(DMApp,self).__init__(parent)
        self.setupUi(self)
        self.webcamButton.clicked[bool].connect(self.runWebCam)
        self.browseButton.clicked.connect(self.openFileNameDialog)
        self.browseFolderButton.clicked.connect(self.openFolderDialog)
        self.retinaButton.clicked[bool].connect(self.setRetinaEnabled)
        self.generateButton.clicked.connect(self.getVideoFrames)
        self.saveButton.clicked.connect(self.saveFileDialog)
        self.maintabWidget.setCurrentIndex(0)
        self.threadpool = QThreadPool()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open file", "",
            "All Files (*);;mp4 Files (*.mp4);;avi Files (*.avi);;jpeg Files (*.jpg);;csv Files (*.csv);;json Files(*.json)",
            options=options)
        filetype = fileName.split('.')[-1]
        if fileName:
            print("Opening " + fileName)
            self.infoLabel.setText("File opened: " + fileName)
            if filetype in self.videofiletypes:
                self.currentFile = vid.Video(filepath=fileName,palette="rgb")
                self.generateButton.setDisabled(False)
                self.startVideoPlayer()
            elif filetype in self.metadatatypes:
                self.metaFileName = fileName
                self.fileType = filetype
                worker = Worker(self.loadCsv)
                worker.signals.finished.connect(self.displayMetaData)
                worker.signals.error.connect(self.showWarning)
                #worker.signals.result()
                self.threadpool.start(worker)
            elif filetype in self.rawvectortypes:
                self.currentFile = fileName
                worker = Worker(self.loadNpy)
                worker.signals.result.connect(self.setCurrentFrames)
                worker.signals.finished.connect(self.fillGallery)
                self.threadpool.start(worker)
                self.infoLabel.setText("File opened: "+ fileName)
                self.generateButton.setText("Loading...")
                self.generateButton.setDisabled(True)
                self.verticalSlider_3.valueChanged.connect(self.fillGallery)
            elif filetype == 'pkl':
                self.currentFile = fileName
                worker = Worker(self.loadPickle)
                worker.signals.result.connect(self.setCurrentFrames)
                worker.signals.finished.connect(self.fillGallery)
                self.threadpool.start(worker)
            elif filetype == 'h5':
                self.currentFile = fileName
                worker = Worker(self.loadhdf5)
                worker.signals.result.connect(self.setCurrentFrames)
                worker.signals.finished.connect(self.fillGallery)
                self.threadpool.start(worker)
            else:
                self.showWarning('File type not supported')

    def openFolderDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        datadir = QFileDialog.getExistingDirectory(self, "Open folder")
        if datadir:
            print("Directory opened:" + datadir)
            self.currentDir = datadir
            worker = Worker(self.createImagesFromFolder)
            worker.signals.result.connect(self.setCurrentFrames)
            worker.signals.finished.connect(self.fillGallery)
            self.threadpool.start(worker)
            self.infoLabel.setText("Folder opened: "+ self.currentDir)
            self.generateButton.setText("Loading...")
            self.generateButton.setDisabled(True)
            self.verticalSlider_3.valueChanged.connect(self.fillGallery)

    def loadhdf5(self):
        currentFrames = []
        hdf5_open = h5py.File(self.currentFile, mode="r")
        try:
            for i in range(len(hdf5_open['vectors'])):
                if 'label' in hdf5_open.keys():
                    v = ImageVector(vector=hdf5_open['vectors'][i],
                        framenum=hdf5_open['framenum'][i],
                        timestamp=hdf5_open['timestamp'][i],
                        label=hdf5_open['label'][i],
                        fixationy=hdf5_open['fixationy'][i],
                        fixationx=hdf5_open['fixationx'][i],
                        retinatype=hdf5_open['retinatype'][i])
                else:
                    v = ImageVector(vector=hdf5_open['vectors'][i])
                currentFrames.append(v)
        except KeyError:
            print("There was a problem with the format of the hdf5 file")
        return currentFrames


    def loadNpy(self):
        currentFrames = []
        with np.load(self.currentFile) as data:
            for d in data:
                print(d.value)
                #frame = im.Image(image=d)
                #currentFrames.append(frame)
        return currentFrames

    def loadPickle(self):
        return utils.loadPickle(self.currentFile)

    def loadCsv(self):
        metadata = pd.read_csv(self.metaFileName,delimiter=";",encoding="utf-8")
#        try:

        # we need a decision engine that decides what to do based on
        # csv headers, throwing an exception only when all options are exhausted

        # image file metadata
        parentfile = metadata['parentfile'].values
        # image and video file metadata
        colortype = metadata['colortype'].values
        # image and vector metadata
        framenum = metadata['framenum'].values
        timestamp = metadata['timestamp'].values
        label = metadata['label'].values
        # vector only metadata
        vector = metadata['vector'].values
        fixationy = metadata['fixationy'].values
        fixationx = metadata['fixationx'].values
        retinatype  metadata['retinatype'].values

        # load data into model here
        for index, im in enumerate(self.currentFrames):
            im.type = imagetype[index]
            im.parent = parentfile[index]
            im.framenum = framenum[index]
            im.colortype = colortype[index]
            im.label = label[index]
            im.fixation = {fixationx[index],fixationy[index]}
#        except KeyError:
#            self.showWarning('There was a problem with the format of the csv')
#        except IndexError:
#            self.showWarning('There is an inequal number of images and metadata records')
#        except TypeError:
#            self.showWarning('Please load images before loading metadata')

    def saveToNpy(self):
        shape = self.currentFrames[0].image.shape
        list = []
        #array_list = np.empty([len(self.currentFrames),shape[0],shape[1],shape[2]])
        for frame in self.currentFrames:
            list.append(frame.image)
            #array_list[index] = frame.image

        np.savez_compressed('testnpy',list)


    def displayMetaData(self, framenum=0):
        self.metadatamodel = QtGui.QStandardItemModel(self)
        currentframe = self.currentFrames[framenum]

        labels = ['name','type','parent file','frame num','color channels',
            'label','fixation x','fixation y']
        items = []
        for label in labels:
            item = QStandardItem(label)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            items.append(item)
        self.metadatamodel.appendColumn(items)

        fields = [currentframe.name,currentframe.type,currentframe.parent,
            currentframe.framenum,currentframe.colortype,currentframe.label,
            currentframe.fixationx,currentframe.fixationy]
        values = []
        for field in fields:
            v = QStandardItem(field)
            values.append(v)
        self.metadatamodel.appendColumn(values)

        self.metadata.setModel(self.metadatamodel)

    def createImagesFromFolder(self):
        currentFrames = []
        for root, dirs, files in os.walk(self.currentDir):
            for file in files:
                print(file)
                filetype = file.split(".")[-1]
                if filetype in {'jpg','png'}:
                    print("Creating image")
                    image = cv2.imread(join(root,file))
                    frame = Image(image=image,filepath=join(root,file))
                    currentFrames.append(frame)
        return currentFrames

    def getVideoFrames(self):
        if self.currentFile:
            worker = Worker(self.currentFile.getFrames)
            worker.signals.result.connect(self.setCurrentFrames)
            worker.signals.finished.connect(self.fillGallery)
            self.threadpool.start(worker)
            self.generateButton.setText("Generating...")
            self.verticalSlider_3.valueChanged.connect(self.fillGallery)
            self.generateButton.setDisabled(True)

    def setCurrentFrames(self, frames):
        self.currentFrames = frames

    #Not currently in use
    def saveFileDialog(self, isHDF5):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Save file","","All Files (*)", options=options)
        filetype = fileName.split(".")[-1]
        if fileName:
            if filetype == 'pkl':
                utils.writePickle(fileName, self.currentFrames)

    def setRetinaEnabled(self, event):
        if event:
            self.isRetinaEnabled = True
        else:
            self.isRetinaEnabled = False

    def startVideoPlayer(self):
        self.videoPlayer = VideoPlayer(self.currentFile,self.isRetinaEnabled,self)
        self.pauseButton.clicked.connect(self.videoPlayer.pause)
        self.startButton.clicked.connect(self.videoPlayer.start)
        self.skipBackButton.clicked.connect(self.videoPlayer.skipBck)
        self.skipForwardButton.clicked.connect(self.videoPlayer.skipFwd)
        self.scrubSlider.valueChanged.connect(self.sendFramePos)
        self.pauseButton_2.clicked.connect(self.videoPlayer.pause)
        self.startButton_2.clicked.connect(self.videoPlayer.start)
        self.skipBackButton_2.clicked.connect(self.videoPlayer.skipBck)
        self.skipForwardButton_2.clicked.connect(self.videoPlayer.skipFwd)
        self.scrubSlider_2.valueChanged.connect(self.sendFramePos)

    def sendFramePos(self):
        framePos = self.scrubSlider.value()
        self.videoPlayer.skip(framePos)

    def runWebCam(self, event):
        if event:
            self.currentFile = 0
            self.startVideoPlayer()
            self.browseButton.setDisabled(True)
            self.browseFolderButton.setDisabled(True)
            self.scrubSlider.setDisabled(True)
        else:
            self.videoPlayer = None
            self.browseButton.setDisabled(False)
            self.browseFolderButton.setDisabled(False)

    def fillGallery(self):
        self.maintabWidget.setCurrentIndex(2)
        self.generateButton.setText("Done!")
        self.verticalSlider_3.setRange(0,len(self.currentFrames)/16)
        labels = self.dataframe_2.findChildren(QtWidgets.QLabel)
        for index, label in enumerate(labels):
            if index < len(self.currentFrames):
                label.setPixmap(ImageProcessing.convertToPixmap(self.currentFrames[index + (index * self.verticalSlider_3.value())].image,320,180))
        numbers = self.dataframe_2.findChildren(QtWidgets.QLCDNumber)
        for index, number in enumerate(numbers):
            if index < len(self.currentFrames):
                number.display(self.currentFrames[index + (index * self.verticalSlider_3.value())].framenum)

    def showWarning(self, error):
        messages = {
        'exceptions.IndexError' : 'There is an inequal number of images and metadata records',
        'exceptions.KeyError' : 'Please load images before loading metadata',
        }
        errormessage = QMessageBox(parent=None)
        errormessage.setStandardButtons(QMessageBox.Ok)
        errormessage.setWindowTitle('Warning')
        errormessage.setIcon(QMessageBox.Warning)
        errormessage.setText(messages[str(error[1])])
        errormessage.exec_()


def main():
    app = QApplication(sys.argv)
    form = DMApp()
    #qtmodern.styles.dark(app)
    #mw = qtmodern.windows.ModernWindow(form)
    #mw.show()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
