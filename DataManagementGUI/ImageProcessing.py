import sys
import os
import numpy as np
import cv2
from PyQt5 import QtGui, QtCore
from QtGui import QImage, QPixmap
from QtCore import Qt
from os.path import join
from model import Image as im, Video as vid
from retinavision.retina import Retina
from retinavision.cortex import Cortex
from retinavision import datadir, utils

def startRetina(cap):
    ret, frame = cap.read()
    retina = Retina()
    retina.loadLoc(join(datadir, "retinas", "ret50k_loc.pkl"))
    retina.loadCoeff(join(datadir, "retinas", "ret50k_coeff.pkl"))
    x = frame.shape[1]/2
    y = frame.shape[0]/2
    fixation = (y,x)
    retina.prepare(frame.shape, fixation)
    return retina, fixation

def createCortex():
    cortex = Cortex()
    lp = join(datadir, "cortices", "Ll.pkl")
    rp = join(datadir, "cortices", "Rl.pkl")
    cortex.loadLocs(lp, rp)
    cortex.loadCoeffs(join(datadir, "cortices", "Lcoeff.pkl"), join(datadir, "cortices", "Rcoeff.pkl"))
    return cortex

def convertToPixmap(frame, x, y):
    rgbImage = cv2.cvtColor(frame,cv2.cv2.COLOR_BGR2RGB)
    converttoQtFormat = QImage(rgbImage.data,rgbImage.shape[1],rgbImage.shape[0],QImage.Format_RGB888)
    pic = converttoQtFormat.scaled(x,y,Qt.KeepAspectRatio)
    pixmap = QPixmap.fromImage(pic)
    return pixmap

def createImagesFromFolder(currentdir):
    currentFrames = []
    for root, dirs, files in os.walk(currentdir):
        path = root.split(os.sep)
        for file in files:
            print(file)
            filetype = file.split(".")[-1]
            if filetype in {'jpg','png'}:
                print("Creating image")
                image = cv2.imread(join(root,file))
                frame = im.Image(image=image,filepath=join(root,file))
                currentFrames.append(frame)
    return currentFrames
