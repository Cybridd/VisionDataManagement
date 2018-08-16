import sys
import os
import numpy as np
import cv2
from PyQt5 import QtGui, QtCore
from QtGui import QImage, QPixmap
from QtCore import Qt
from os.path import join
from model import Image, Video
from retinavision.retina import Retina
from retinavision.cortex import Cortex
from retinavision import datadir, utils

def prepareLiveRetina(cap):
    retina = startRetina()
    ret, frame = cap.read()
    x = frame.shape[1]/2
    y = frame.shape[0]/2
    fixation = (y,x)
    retina.prepare(frame.shape, fixation)
    return retina, fixation

def startRetina():
    retina = Retina()
    retina.loadLoc(join(datadir, "retinas", "ret50k_loc.pkl"))
    retina.loadCoeff(join(datadir, "retinas", "ret50k_coeff.pkl"))
    return retina

def getBackProjection(R,V,fix):
    backshape = [720,1280,V.shape[-1]] # fixed size for the case of this app
    return R.backproject(V,backshape,fix)

def createCortex():
    cortex = Cortex()
    lp = join(datadir, "cortices", "50k_Lloc_tight.pkl")
    rp = join(datadir, "cortices", "50k_Rloc_tight.pkl")
    cortex.loadLocs(lp, rp)
    cortex.loadCoeffs(join(datadir, "cortices", "50k_Lcoeff_tight.pkl"), join(datadir, "cortices", "50k_Rcoeff_tight.pkl"))
    return cortex

def convertToPixmap(frame, x, y):
    if frame.shape[-1] == 3:
        frame = cv2.cvtColor(frame,cv2.cv2.COLOR_BGR2RGB)
        format = QImage.Format_RGB888
    else:
        format = QImage.Format_Grayscale8
    converttoQtFormat = QImage(frame.data,frame.shape[1],frame.shape[0],format)
    pic = converttoQtFormat.scaled(x,y,Qt.KeepAspectRatio)
    pixmap = QPixmap.fromImage(pic)
    return pixmap

# moved into main, may leave there
def createImagesFromFolder(currentDir):
    currentFrames = []
    count = 1
    for root, dirs, files in os.walk(currentDir):
        for file in files:
            print(file)
            filetype = file.split(".")[-1]
            if filetype in {'jpg','png'}:
                print("Creating image")
                image = cv2.imread(join(root,file))
                frame = Image(image=image,filepath=join(root,file),framenum=count)
                currentFrames.append(frame)
                count += 1
    return currentFrames
