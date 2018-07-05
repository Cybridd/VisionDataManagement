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
        MainWindow.resize(786, 461)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.dataframe = QtWidgets.QFrame(self.centralwidget)
        self.dataframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.dataframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.dataframe.setObjectName("dataframe")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.dataframe)
        self.verticalLayout.setObjectName("verticalLayout")
        self.videoframe = QtWidgets.QFrame(self.dataframe)
        self.videoframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.videoframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.videoframe.setObjectName("videoframe")
        self.verticalLayout.addWidget(self.videoframe)
        self.scrubframe = QtWidgets.QFrame(self.dataframe)
        self.scrubframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.scrubframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.scrubframe.setObjectName("scrubframe")
        self.verticalLayout.addWidget(self.scrubframe)
        self.horizontalLayout.addWidget(self.dataframe)
        self.buttonframe = QtWidgets.QFrame(self.centralwidget)
        self.buttonframe.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.buttonframe.setFrameShadow(QtWidgets.QFrame.Raised)
        self.buttonframe.setObjectName("buttonframe")
        self.horizontalLayout.addWidget(self.buttonframe)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 786, 21))
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

