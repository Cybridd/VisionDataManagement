# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design.ui'
#
# Created by: PyQt5 UI code generator 5.7.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1068, 710)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.dataframe = QtWidgets.QFrame(self.centralwidget)
        self.dataframe.setGeometry(QtCore.QRect(9, 9, 771, 651))
        self.dataframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.dataframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.dataframe.setObjectName("dataframe")
        self.videoframe = QtWidgets.QFrame(self.dataframe)
        self.videoframe.setGeometry(QtCore.QRect(10, 10, 751, 461))
        self.videoframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.videoframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.videoframe.setObjectName("videoframe")
        self.label = QtWidgets.QLabel(self.videoframe)
        self.label.setGeometry(QtCore.QRect(210, 10, 341, 211))
        self.label.setText("")
        self.label.setObjectName("label")
        self.scrubframe = QtWidgets.QFrame(self.dataframe)
        self.scrubframe.setGeometry(QtCore.QRect(10, 480, 751, 161))
        self.scrubframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.scrubframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.scrubframe.setObjectName("scrubframe")
        self.scrubSlider = QtWidgets.QSlider(self.scrubframe)
        self.scrubSlider.setGeometry(QtCore.QRect(-1, 10, 701, 22))
        self.scrubSlider.setOrientation(QtCore.Qt.Horizontal)
        self.scrubSlider.setObjectName("scrubSlider")
        self.frameNum = QtWidgets.QLCDNumber(self.scrubframe)
        self.frameNum.setGeometry(QtCore.QRect(710, 10, 31, 23))
        self.frameNum.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.frameNum.setSmallDecimalPoint(False)
        self.frameNum.setObjectName("frameNum")
        self.pauseButton = QtWidgets.QPushButton(self.scrubframe)
        self.pauseButton.setGeometry(QtCore.QRect(310, 40, 75, 23))
        self.pauseButton.setCheckable(True)
        self.pauseButton.setObjectName("pauseButton")
        self.buttonframe = QtWidgets.QFrame(self.centralwidget)
        self.buttonframe.setGeometry(QtCore.QRect(788, 9, 271, 651))
        self.buttonframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.buttonframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.buttonframe.setObjectName("buttonframe")
        self.browseButton = QtWidgets.QPushButton(self.buttonframe)
        self.browseButton.setGeometry(QtCore.QRect(20, 10, 21, 23))
        self.browseButton.setObjectName("browseButton")
        self.webcamButton = QtWidgets.QPushButton(self.buttonframe)
        self.webcamButton.setGeometry(QtCore.QRect(70, 10, 75, 23))
        self.webcamButton.setCheckable(True)
        self.webcamButton.setChecked(False)
        self.webcamButton.setAutoRepeat(False)
        self.webcamButton.setDefault(False)
        self.webcamButton.setObjectName("webcamButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1068, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pauseButton.setText(_translate("MainWindow", "Pause"))
        self.browseButton.setText(_translate("MainWindow", "..."))
        self.webcamButton.setText(_translate("MainWindow", "WebCam"))

