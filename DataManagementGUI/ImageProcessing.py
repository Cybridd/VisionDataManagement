import sys
import os
import numpy as np
import cv2
from os.path import join
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
