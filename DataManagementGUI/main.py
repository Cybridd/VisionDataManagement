import sys, traceback
import os
import design
import cv2
import time
import pandas as pd
import ImageProcessing
from os.path import join
from model import Image as im, Video as vid
from PyQt5 import QtCore, QtGui, QtWidgets
from QtCore import *
from QtGui import *
from QtWidgets import *

#TODO metadata editing, deleting files, export for DCNN,
# Give to Worker - Image/Video object creation, image saving/exporting, display updating

class WorkerSignals(QObject):

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            start = time.time()
            result = self.fn(*self.args)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            end = time.time()
            print("This operation required " + str(end - start) + " seconds.")
            self.signals.finished.emit()

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

    def __init__(self,parent=None):
        super(DMApp,self).__init__(parent)
        self.setupUi(self)
        self.webcamButton.clicked[bool].connect(self.runWebCam)
        self.browseButton.clicked.connect(self.openFileNameDialog)
        self.browseFolderButton.clicked.connect(self.openFolderDialog)
        self.retinaButton.clicked[bool].connect(self.setRetinaEnabled)
        self.generateButton.clicked.connect(self.getVideoFrames)
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

    def loadCsv(self):
        metadata = pd.read_csv(self.metaFileName)
        if "np.array" in metadata.dtypes:
            #we need to generate the images from CSV
            pass
        else:
            try:
                metadata = metadata.set_index("imagename", drop=False)
                imagename = metadata['imagename'].values
                imagetype = metadata['imagetype'].values
                parentfile = metadata['parentfile'].values
                framenum = metadata['framenum'].values
                colortype = metadata['colortype'].values
                label = metadata['label'].values
                fixationx = metadata['fixationx'].values
                fixationy = metadata['fixationy'].values
                for index, im in enumerate(self.currentFrames):
                    im.type = imagetype[index]
                    im.parent = parentfile[index]
                    im.frameNum = framenum[index]
                    im.colortype = colortype[index]
                    im.label = label[index]
                    im.fixation = {fixationx[index],fixationy[index]}
            except KeyError:
                self.showWarning('There was a problem with the format of the csv')
            #except IndexError:
            #    self.showWarning('There is an inequal number of images and metadata records')


    def displayMetaData(self):
        #self.metadatamodel = QtGui.QStandardItemModel(self)
        #file = open(self.metaFileName,'rb')
        #reader = csv.reader(file)
        #self.metadata.clear()
        #for row in reader:
        #    items = [
        #        QStandardItem(field)
        #        for field in row
        #    ]
        #    self.metadatamodel.appendRow(items)
        #self.metadata.setModel(self.metadatamodel)
        pass

    def createImagesFromFolder(self):
        currentFrames = []
        for root, dirs, files in os.walk(self.currentDir):
            for file in files:
                print(file)
                filetype = file.split(".")[-1]
                if filetype in {'jpg','png'}:
                    print("Creating image")
                    image = cv2.imread(join(root,file))
                    frame = im.Image(image=image,filepath=join(root,file))
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
        fileName, _ = QFileDialog.getSaveFileName(self,"Save file","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            print(fileName)

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
                number.display(self.currentFrames[index + (index * self.verticalSlider_3.value())].frameNum)

    def showWarning(self, error):
        messages = {
        'exceptions.IndexError' : 'There is an inequal number of images and metadata records',
        }
        errormessage = QMessageBox(parent=None)
        errormessage.setStandardButtons(QMessageBox.Ok)
        errormessage.setWindowTitle('Warning')
        errormessage.setIcon(QMessageBox.Warning)
        errormessage.setText(str(error[1]))
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
