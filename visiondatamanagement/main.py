"""
Created on 7/5/2018 19:04

Main class for the VDM application.

@author: Connor Fulton
"""

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
        # on load, connect UI elements to their respective functions
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
        # sort gallery items by name so they can be filled easily
        self.labels.sort(key=lambda label: label.objectName())
        # connect gallery item click signals to their respective functions
        for i in xrange(len(self.labels)):
            self.labels[i].clicked.connect(self.displayMetaData)
            self.labels[i].unhighlighted.connect(self.removeHighlighted)
        self.numbers = self.dataframe_2.findChildren(QtWidgets.QLCDNumber)
        # also sort the frame number labels
        self.numbers.sort(key=lambda number: number.objectName())
        self.maintabWidget.setCurrentIndex(0)
        # instantiate a thread pool
        self.threadpool = QThreadPool()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open file", "",
            "All Files (*);;mp4 Files (*.mp4);;avi Files (*.avi);;jpeg Files (*.jpg);;csv Files (*.csv);;HDF5 Files(*.h5)",
            options=options)
        # only continue if a name has been specified
        if fileName:
            self.openFile(fileName)

    def openFile(self,filename):
        filetype = filename.split('.')[-1]
        self.generateButton.setText("Loading...")
        self.infoLabel.setText("File opened: " + filename)
        print("Opening " + filename)
        # start the video player or start a worker thread depending on file type
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
            # invalid file type selected
            self.showWarning('FileType')

    def openFolderDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        datadir = QFileDialog.getExistingDirectory(self, "Open folder")
        # only continue if a folder was chosen
        if datadir:
            print("Directory opened:" + datadir)
            self.currentDir = datadir
            self.startWorker(ip.createImagesFromFolder,self.setCurrentFrames,
                self.fillGallery,self.currentDir)
            self.infoLabel.setText("Folder opened: "+ self.currentDir)
            self.generateButton.setText("Loading...")
            self.generateButton.setDisabled(True)

    def startWorker(self,func,resultfunc=None,finishedfunc=None,*args):
        """Instantiates a Worker, adds it to the pool and starts it

        Parameters
        ----------
        func : function of task to be performed
        resultfunc : function to receive return value
        finishedfunc : function to be called on finished signals
        args : arguments to be passed with the task function
        """
        worker = Worker(func,*args)
        if resultfunc: worker.signals.result.connect(resultfunc)
        if finishedfunc: worker.signals.finished.connect(finishedfunc)
        worker.signals.error.connect(self.showWarning)
        self.threadpool.start(worker)

    def loadPickle(self):
        return utils.loadPickle(self.currentFile)

    def displayMetaData(self,framenum=0):
        """Gets metadata for selected frame and adds it to the displayed model

        Parameters
        ----------
        framenum : index of object whose metadata is required
        """

        # only proceed if frames are available and valid framnum is chosen
        if self.currentFrames and framenum >= 0 and framenum < len(self.currentFrames):
            # instantiate a new QStandardItemModel which will hold the data
            self.metadatamodel = QtGui.QStandardItemModel(self)
            currentframe = self.currentFrames[framenum]
            # get attribute names of object in question
            labels = dir(self.currentFrames[0])
            items = []
            values = []
            for label in labels:
                # add attribute names to first column
                item = QStandardItem(label.replace("_",""))
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                items.append(item)
                # add attribute values to second column
                value = QStandardItem(str(getattr(currentframe, label)))
                values.append(value)

            self.metadatamodel.appendColumn(items)
            self.metadatamodel.appendColumn(values)
            # set model to that of the metadata table gui element
            self.metadata.setModel(self.metadatamodel)
            # set the image displayed in the large display to the current image
            self.biglabel.setPixmap(ip.convertToPixmap(currentframe.image,1280,720))
            # add this frame to the list of highlighted images
            if framenum not in self.highlightedframes:
                self.highlightedframes.append(int(framenum))

    def removeHighlighted(self,framenum):
        """Removes selected frame from list of highlighted frames

        Parameters
        ----------
        framenum : index of object which is no longer highlighted/selected
        """
        #print("highlighted frames: " + ' '.join(str(e) for e in self.highlightedframes))
        if framenum in self.highlightedframes:
            #print("removing " + str(framenum))
            self.highlightedframes.remove(framenum)
        #print("remaining frames: " + ' '.join(str(e) for e in self.highlightedframes))

    def saveMetaData(self,framenum):
        """Saves metadata for selected frame, retrieving from metadata table

        Parameters
        ----------
        framenum : index of object whose metadata must be saved
        """
        if self.currentFrames:
            # if we're on the main tab, this frame is the target
            if self.maintabWidget.currentIndex() == 2:
                targetframes = [self.currentFrames[i] for i in self.highlightedframes]
            # if we're on the gallery page, the target is all the highlighted frames
            else:
                targetframes = [f for f in self.currentFrames if f.framenum == self.getCurrentFrameNum()]
            for targetframe in targetframes:
                # scan the metadata table
                for i in xrange(self.metadatamodel.rowCount()):
                    field = str(self.metadatamodel.item(i,0).text())
                    value = str(self.metadatamodel.item(i,1).text())
                    # only store changes to the label in the current version
                    if field == 'label':
                        setattr(targetframe, field, value)

    def getVideoFrames(self):
        """Requests the Video object to break itself into frames"""
        if self.currentFile:
            # this is a lengthy process, use a worker
            self.startWorker(self.currentFile.getFrames,self.setCurrentFrames,self.fillGallery)
            self.generateButton.setText("Generating...")
            self.verticalSlider_3.valueChanged.connect(self.fillGallery)
            self.generateButton.setDisabled(True)

    def setCurrentFrames(self,frames):
        """Sets the global list of current frames to the argument given

        Connected to the result signal of Worker objects so we can receive
         the returned frames

         Parameters
         -------
         frames : list of objects that must be set as current frames
         """
        self.currentFrames = frames
        self.verticalSlider_3.valueChanged.connect(self.fillGallery)
        self.generateButton.setText("Done!")
        numframes = len(self.currentFrames)
        # adjust the range of the gallery slider depending on length of list
        self.verticalSlider_3.setRange(0,numframes/16)
        # reset the video player when new things are imported
        self.startVideoPlayer()

    def getCurrentFrameNum(self):
        """Searches the metadata table for the framenum whose data is currently displayed

        Returns
        -------
        targetframe : frame number found in metadata table
        """
        for i in xrange(self.metadatamodel.rowCount()):
            if self.metadatamodel.item(i,0).text() == 'framenum':
                targetframe = int(self.metadatamodel.item(i,1).text())
        return targetframe

    def selectAll(self):
        """'Selects' all the items in the gallery by adding them to the highlighted frames list"""
        if self.currentFrames:
            for label in self.labels:
                # highlight all the gallery items
                if label.pixmap:
                    label.makeHighlighted()
            self.maintabWidget.setCurrentIndex(2)
            self.highlightedframes = range(len(self.currentFrames))

    def deleteFrame(self):
        """Deletes selected frames from the list"""
        if self.currentFrames:
            # if we're on the gallery tab, the target is all highlighted frames
            if self.maintabWidget.currentIndex() == 2:
                print("Deleting frames: " + ' '.join(str(e) for e in self.highlightedframes))
                targetframes = [self.currentFrames[i] for i in self.highlightedframes]
            # if we're on the main tab, the target is the currently displayed frame
            else:
                targetframes = [f for f in self.currentFrames if f.framenum == self.getCurrentFrameNum()]
            self.currentFrames = [f for f in self.currentFrames if f not in targetframes]
            # update after changes
            self.fillGallery()
            self.updateVideoPlayer()

    def closeFile(self):
        """Closes the current project by deleting the current frames and file reference"""
        if self.currentFile: self.currentFile = None
        if self.currentFrames:
            self.currentFrames = []
            self.fillGallery()
            self.updateVideoPlayer()

    def updateVideoPlayer(self):
        """Updates the video player after changes to the current frames have been made"""
        self.videoPlayer.frames = self.currentFrames
        self.videoPlayer.maxFrames = len(self.currentFrames) - 1
        #self.videoPlayer.framePos = 0
        #self.videoPlayer.nextFrame()
        self.videoPlayer.setCurrent()

    def saveFileDialog(self):
        fileName, _ = QFileDialog.getSaveFileName(self,"Save file","","csv (*.csv);;HDF5 (*.h5);;pickle (*.pkl)")#, options=options
        filetype = fileName.split(".")[-1]
        # only proceed if a file name was chosen
        if fileName and self.currentFrames:
            self.exportfilename = fileName
            # start different workers depending on file type
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
                # invalid file type specified
                self.showWarning('FileType')

    def setRetinaEnabled(self, event):
        """Sets the boolean for retina use and (de)activates relevant buttons"""
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
        """Instantiates and initializes the video player and connects relevant buttons"""
        self.videoPlayer = VideoPlayer(self.currentFile,self.isRetinaEnabled,self,webcammode)
        self.pauseButton.clicked.connect(self.videoPlayer.pause)
        self.startButton.clicked.connect(self.videoPlayer.start)
        self.pauseButton_2.clicked.connect(self.videoPlayer.pause)
        self.startButton_2.clicked.connect(self.videoPlayer.start)
        # don't connect all buttons if in webcam mode
        if not webcammode:
            self.skipBackButton.clicked.connect(self.videoPlayer.skipBck)
            self.skipForwardButton.clicked.connect(self.videoPlayer.skipFwd)
            self.scrubSlider.valueChanged.connect(self.sendFramePos)
            self.skipBackButton_2.clicked.connect(self.videoPlayer.skipBck)
            self.skipForwardButton_2.clicked.connect(self.videoPlayer.skipFwd)
            self.scrubSlider_2.valueChanged.connect(self.sendFramePos)

    def sendFramePos(self):
        """Passes the frame index to the video player"""
        framePos = self.scrubSlider.value()
        self.videoPlayer.skip(framePos)

    def runWebCam(self,event):
        """Starts video player in webcam mode and deactivates relevant buttons"""
        if event:
            self.currentFile = 0
            self.startVideoPlayer(webcammode=True)
            self.browseButton.setDisabled(True)
            self.browseFolderButton.setDisabled(True)
            self.scrubSlider.setDisabled(True)
            self.skipBackButton.setDisabled(True)
            self.skipForwardButton.setDisabled(True)
        else:
            self.skipBackButton.setDisabled(False)
            self.skipForwardButton.setDisabled(False)
            if self.currentFrames:
                self.startVideoPlayer()
            else:
                self.videoPlayer = None
            self.browseButton.setDisabled(False)
            self.browseFolderButton.setDisabled(False)


    def fillGallery(self):
        """Updates the gallery items and frame number labels"""
        if self.maintabWidget.currentIndex() == 0:
            self.maintabWidget.setCurrentIndex(2)
        for i in xrange(len(self.labels)):
            if i < len(self.currentFrames):
                tempindex = i + (16 * self.verticalSlider_3.value())
                if tempindex < len(self.currentFrames):
                    currentframe = self.currentFrames[tempindex]
                    self.labels[i].setPixmap(ip.convertToPixmap(currentframe.image,320,180,
                        currentframe.vectortype == 'BGR'))
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
            self.labels[i].notHighlighted()
        self.highlightedframes = []

    def showWarning(self,error):
        """Helps generate message boxes with relevant messages"""
        if isinstance(error, tuple):
            messagekey = str(error[1])
        else:
            messagekey = error
        messages = {
        'exceptions.IndexError' : 'There is an inequal number of images and metadata records',
        '1L' : 'There was a problem with the format of the metadata',
        'NoFrames' : 'Please load images before loading metadata',
        'HDF5Format' : 'There was a problem with the format of the HDF5 file',
        'CSVFormat' : 'There was a problem with the format of the CSV file',
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
    app.setStyle('Fusion')
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
