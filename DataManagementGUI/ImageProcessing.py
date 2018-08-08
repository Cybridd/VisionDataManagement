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

def getBackProjection(R,V,shape,fix):
    return R.backproject(V,shape,fix)

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
    converttoQtFormat = QImage(frame.data,frame.shape[1],frame.shape[0],QImage.Format_RGB888)
    pic = converttoQtFormat.scaled(x,y,Qt.KeepAspectRatio)
    pixmap = QPixmap.fromImage(pic)
    return pixmap

# moved into main, may leave there
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
