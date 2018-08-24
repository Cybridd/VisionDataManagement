import sys
import design
import processing as ip
from customwidgets import VideoPlayer, ClickLabel
from model import Video
from worker import Worker
from retinavision import utils
from PyQt5 import QtCore, QtGui, QtWidgets
from QtCore import *
from QtGui import *
from QtWidgets import *

#TODO TESTING, maybe adding vector generation from raw data

class DMApp(QMainWindow, design.Ui_MainWindow):

    fileName = None
    currentDir = None
    currentFile = None
    currentFrames = None
    metaFileName = None
    metadatamodel = None
    videoPlayer = None
    isRetinaEnabled = False
    highlightedframes = []
    videofiletypes = {'mp4','avi'}
    metadatatypes = {'csv'}
    rawvectortypes = {'npy','npz'}

    def __init__(self,parent=None):
        super(DMApp,self).__init__(parent)
        self.setupUi(self)
        self.webcamButton.clicked[bool].connect(self.runWebCam)
        self.browseButton.clicked.connect(self.openFileNameDialog)
        self.browseFolderButton.clicked.connect(self.openFolderDialog)
        self.retinaButton.clicked[bool].connect(self.setRetinaEnabled)
        self.generateButton.clicked.connect(self.getVideoFrames)
        self.exportButton.clicked.connect(self.saveFileDialog)
        self.saveButton.clicked.connect(self.saveMetaData)
        self.deleteButton.clicked.connect(self.deleteFrame)
        self.actionExport.triggered.connect(self.saveFileDialog)
        self.actionFile.triggered.connect(self.openFileNameDialog)
        self.actionFolder.triggered.connect(self.openFolderDialog)
        self.actionClose.triggered.connect(self.closeFile)
        self.actionSelect_All.triggered.connect(self.selectAll)
        self.actionDelete_Selection.triggered.connect(self.deleteFrame)
        self.actionExit.triggered.connect(self.closeApp)
        self.labels = self.dataframe_2.findChildren(ClickLabel)
        self.labels.sort(key=lambda label: label.objectName())
        for i in xrange(len(self.labels)):
            self.labels[i].clicked.connect(self.displayMetaData)
            self.labels[i].unhighlighted.connect(self.removeHighlighted)
        self.numbers = self.dataframe_2.findChildren(QtWidgets.QLCDNumber)
        self.numbers.sort(key=lambda number: number.objectName())
        self.maintabWidget.setCurrentIndex(0)
        self.threadpool = QThreadPool()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open file", "",
            "All Files (*);;mp4 Files (*.mp4);;avi Files (*.avi);;jpeg Files (*.jpg);;csv Files (*.csv);;HDF5 Files(*.h5)",
            options=options)
        if fileName:
            self.openFile(fileName)

    def openFile(self,filename):
        filetype = filename.split('.')[-1]
        self.generateButton.setText("Loading...")
        self.infoLabel.setText("File opened: " + filename)
        print("Opening " + filename)
        if filetype in self.videofiletypes:
            self.currentFile = Video(filepath=filename,colortype="rgb")
            self.generateButton.setText("Generate images from video")
            self.generateButton.setDisabled(False)
            self.startVideoPlayer()
        elif filetype in self.metadatatypes:
            self.metafilename = filename
            self.startWorker(ip.loadCsv,self.setCurrentFrames,self.fillGallery,
                self.metafilename,self.currentFrames)
        elif filetype == 'pkl':
            self.currentFile = filename
            self.startWorker(ip.loadPickle,self.setCurrentFrames,self.fillGallery,
                self.currentFile)
        elif filetype == 'h5':
            self.currentFile = filename
            self.startWorker(ip.loadhdf5,self.setCurrentFrames,self.fillGallery,
                self.currentFile,self.currentFrames)
        else:
            self.showWarning('FileType')

    def openFolderDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        datadir = QFileDialog.getExistingDirectory(self, "Open folder")
        if datadir:
            print("Directory opened:" + datadir)
            self.currentDir = datadir
            self.startWorker(ip.createImagesFromFolder,self.setCurrentFrames,
                self.fillGallery,self.currentDir)
            self.infoLabel.setText("Folder opened: "+ self.currentDir)
            self.generateButton.setText("Loading...")
            self.generateButton.setDisabled(True)

    def startWorker(self,func,resultfunc=None,finishedfunc=None,*args):
        worker = Worker(func,*args)
        if resultfunc: worker.signals.result.connect(resultfunc)
        if finishedfunc: worker.signals.finished.connect(finishedfunc)
        worker.signals.error.connect(self.showWarning)
        self.threadpool.start(worker)

    def loadPickle(self):
        return utils.loadPickle(self.currentFile)

    def displayMetaData(self,framenum=0):
        if self.currentFrames and framenum >= 0 and framenum < len(self.currentFrames):
            self.metadatamodel = QtGui.QStandardItemModel(self)
            currentframe = self.currentFrames[framenum]

            labels = dir(self.currentFrames[0])
            items = []
            values = []
            for label in labels:
                item = QStandardItem(label)
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                items.append(item)
                value = QStandardItem(str(getattr(currentframe, label)))
                values.append(value)

            self.metadatamodel.appendColumn(items)
            self.metadatamodel.appendColumn(values)
            self.metadata.setModel(self.metadatamodel)

            self.biglabel.setPixmap(ip.convertToPixmap(currentframe.image,1280,720))
            self.highlightedframes.append(int(framenum))

    def removeHighlighted(self,framenum):
        print("highlighted frames: " + ' '.join(str(e) for e in self.highlightedframes))
        if framenum in self.highlightedframes:
            print("removing " + str(framenum))
            self.highlightedframes.remove(framenum)
        print("remaining frames: " + ' '.join(str(e) for e in self.highlightedframes))
    def saveMetaData(self,framenum):
        if self.maintabWidget.currentIndex() == 2:
            targetframes = [self.currentFrames[i] for i in self.highlightedframes]
        else:
            targetframes = [f for f in self.currentFrames if f.framenum == self.getCurrentFrameNum()]
        for targetframe in targetframes:
            for i in xrange(self.metadatamodel.rowCount()):
                field = str(self.metadatamodel.item(i,0).text())
                value = str(self.metadatamodel.item(i,1).text())
                if field == 'label':
                    setattr(targetframe, field, value)

    def getVideoFrames(self):
        if self.currentFile:
            self.startWorker(self.currentFile.getFrames,self.setCurrentFrames,self.fillGallery)
            self.generateButton.setText("Generating...")
            self.verticalSlider_3.valueChanged.connect(self.fillGallery)
            self.generateButton.setDisabled(True)

    def setCurrentFrames(self,frames):
        self.currentFrames = frames
        self.verticalSlider_3.valueChanged.connect(self.fillGallery)
        self.generateButton.setText("Done!")
        numframes = len(self.currentFrames)
        self.verticalSlider_3.setRange(0,numframes/16)
        self.startVideoPlayer()

    def getCurrentFrameNum(self):
        for i in xrange(self.metadatamodel.rowCount()):
            if self.metadatamodel.item(i,0).text() == 'framenum':
                targetframe = int(self.metadatamodel.item(i,1).text())
        return targetframe

    def selectAll(self):
        if self.currentFrames:
            for label in self.labels:
                if label.pixmap:
                    label.makeHighlighted()
            self.maintabWidget.setCurrentIndex(2)
            self.highlightedframes = range(len(self.currentFrames))

    def deleteFrame(self):
        if self.currentFrames:
            if self.maintabWidget.currentIndex() == 2:
                print("Deleting frames: " + ' '.join(str(e) for e in self.highlightedframes))
                targetframes = [self.currentFrames[i] for i in self.highlightedframes]
            else:
                targetframes = [f for f in self.currentFrames if f.framenum == self.getCurrentFrameNum()]
            self.currentFrames = [f for f in self.currentFrames if f not in targetframes]
            for label in self.labels:
                label.notHighlighted()
            self.highlightedframes = []
            self.fillGallery()
            self.updateVideoPlayer()

    def closeFile(self):
        if self.currentFile: self.currentFile = None
        if self.currentFrames:
            self.currentFrames = []
            self.fillGallery()
            self.updateVideoPlayer()

    def updateVideoPlayer(self):
        self.videoPlayer.frames = self.currentFrames
        self.videoPlayer.maxFrames = len(self.currentFrames) - 1
        #self.videoPlayer.framePos = 0
        #self.videoPlayer.nextFrame()
        self.videoPlayer.setCurrent()

    def saveFileDialog(self):
        fileName, _ = QFileDialog.getSaveFileName(self,"Save file","","csv (*.csv);;HDF5 (*.h5);;pickle (*.pkl)")#, options=options
        filetype = fileName.split(".")[-1]
        if fileName and self.currentFrames:
            self.exportfilename = fileName
            if filetype == 'pkl':
                utils.writePickle(fileName, self.currentFrames)
            elif filetype == 'h5':
                self.startWorker(ip.saveHDF5,None,self.generateButton.setText("Done!"),
                    self.exportfilename,self.currentFrames)
                self.generateButton.setText("Saving to HDF5...")
            elif filetype == 'csv':
                self.startWorker(ip.saveCSV,None,None,self.exportfilename,self.currentFrames)
                self.generateButton.setText("Saving to CSV...")
            else:
                self.showWarning('FileType')

    def setRetinaEnabled(self, event):
        if event:
            self.isRetinaEnabled = True
            self.browseButton.setDisabled(True)
            self.browseFolderButton.setDisabled(True)
            self.actionFile.setDisabled(True)
            self.actionFolder.setDisabled(True)
        else:
            self.isRetinaEnabled = False
            self.browseButton.setDisabled(False)
            self.browseFolderButton.setDisabled(False)
            self.actionFile.setDisabled(False)
            self.actionFolder.setDisabled(False)

    def startVideoPlayer(self, webcammode=False):
        self.videoPlayer = VideoPlayer(self.currentFile,self.isRetinaEnabled,self,webcammode)
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

    def runWebCam(self,event):
        if event:
            self.currentFile = 0
            self.startVideoPlayer(webcammode=True)
            self.browseButton.setDisabled(True)
            self.browseFolderButton.setDisabled(True)
            self.scrubSlider.setDisabled(True)
        else:
            if self.currentFrames:
                self.startVideoPlayer()
            self.browseButton.setDisabled(False)
            self.browseFolderButton.setDisabled(False)

    def fillGallery(self):
        if self.maintabWidget.currentIndex() == 0:
            self.maintabWidget.setCurrentIndex(2)
        for i in xrange(len(self.labels)):
            if i < len(self.currentFrames):
                tempindex = i + (16 * self.verticalSlider_3.value())
                if tempindex < len(self.currentFrames):
                    currentframe = self.currentFrames[tempindex]
                    #print("Adding image " +  str(tempindex))
                    self.labels[i].setPixmap(ip.convertToPixmap(currentframe.image,320,180))
                    self.labels[i].setIndex(tempindex)
                    self.numbers[i].display(currentframe.framenum)
                else:
                    self.labels[i].clear()
                    self.labels[i].setIndex(-1)
                    self.numbers[i].display(0)
            else:
                self.labels[i].clear()
                self.labels[i].setIndex(-1)
                self.numbers[i].display(0)

    def showWarning(self,error):
        if isinstance(error, tuple):
            messagekey = str(error[1])
        else:
            messagekey = error
        messages = {
        'exceptions.IndexError' : 'There is an inequal number of images and metadata records',
        '1L' : 'There was a problem with the format of the metadata',
        'NoFrames' : 'Please load images before loading metadata',
        'HDF5Format' : 'There was a problem with the format of the HDF5 file',
        'FileType' : 'File type not supported',
        'InvalidFrameNum' : 'Frame number must be an integer'
        }
        errormessage = QMessageBox(parent=None)
        errormessage.setStandardButtons(QMessageBox.Ok)
        errormessage.setWindowTitle('Warning')
        errormessage.setIcon(QMessageBox.Warning)
        errormessage.setText(messages[messagekey])
        errormessage.exec_()

    def closeApp(self):
        sys.exit()


def main():
    app = QApplication(sys.argv)
    form = DMApp()
    #qtmodern.styles.dark(app)
    #mw = qtmodern.windows.ModernWindow(form)
    #mw.show()
    app.setStyle('Fusion')
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
