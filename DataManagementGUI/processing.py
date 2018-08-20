import sys
import os
import numpy as np
import pandas as pd
import cv2
import h5py
import multiprocessing as mp
from PyQt5 import QtGui, QtCore
from QtGui import QImage, QPixmap
from QtCore import Qt
from os.path import join
from model import Image, ImageVector, Video
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

def loadhdf5(filename, frames):
    currentFrames = frames if frames else []
    hdf5_open = h5py.File(filename, mode="r")
    R = startRetina()
    if R._cudaRetina: print("Using CUDA")
    print(hdf5_open.keys())
    print(len(hdf5_open))
    #cpucount = mp.cpu_count() - 1 if mp.cpu_count() < 32 else mp.cpu_count() / 2
    #pool = mp.Pool(cpu_count)
    #partial_getBackproject = partial(getBackProjection, R=R,)
    #hdf5_open.
    count = 1
    if 'vector' in hdf5_open.keys():
        for i in xrange(len(hdf5_open['vector'])):
            if 'retinatype' in hdf5_open.keys():
                v = ImageVector(vector=hdf5_open['vector'][i],
                    label=hdf5_open['label'][i],
                    fixationy=int(hdf5_open['fixationy'][i]),
                    fixationx=int(hdf5_open['fixationx'][i]),
                    retinatype=hdf5_open['retinatype'][i])
            else:
                v = ImageVector(vector=hdf5_open['vector'][i])
            v.framenum = int(hdf5_open['framenum'][i]) if 'framenum' in hdf5_open.keys() else count
            v._timestamp = hdf5_open['timestamp'][i] if 'timestamp' in hdf5_open.keys() else None
            count += 1
            v.image = getBackProjection(R,v._vector,fix=(v.fixationy,v.fixationx))
            print(v.image.shape)
            currentFrames.append(v)
#        images = pool.starmap(getBackProjection)

    else:
        raise Exception('HDF5Format')
    return currentFrames

def loadHDF5Data(data):
    frames = []
    count = 1
    v = ImageVector(vector=hdf5_open['vector'][i],
        label=hdf5_open['label'][i],
        fixationy=int(hdf5_open['fixationy'][i]),
        fixationx=int(hdf5_open['fixationx'][i]),
        retinatype=hdf5_open['retinatype'][i])
    v.framenum = int(hdf5_open['framenum'][i]) if 'framenum' in hdf5_open.keys() else count
    v._timestamp = hdf5_open['timestamp'][i] if 'timestamp' in hdf5_open.keys() else None
    count += 1
    v.image = getBackProjection(R,v._vector,fix=(v.fixationy,v.fixationx))
    frames.append(v)
    return frames



def saveHDF5(exportname, frames):
    vectors, labels, framenums, timestamps, fixationY, fixationX, retinatypes = ([] for i in range(7))
    hdf5_file = h5py.File(exportname, mode='w')
    currentframe = None
    for i in xrange(len(frames)):
        currentframe = frames[i]
        vectors.append(currentframe._vector)
        labels.append(currentframe.label)
        framenums.append(currentframe.framenum)
        timestamps.append(currentframe._timestamp)
        fixationY.append(currentframe.fixationy)
        fixationX.append(currentframe.fixationx)
        retinatypes.append(currentframe.retinatype)

    hdf5_file.create_dataset("vector",(len(vectors),len(currentframe._vector),currentframe._vector.shape[-1]),np.float64)
    hdf5_file.create_dataset("label",(len(labels),1),"S20")
    hdf5_file.create_dataset("framenum",(len(labels),1),np.int16)
    hdf5_file.create_dataset("timestamp",(len(labels),1),"S11")
    hdf5_file.create_dataset("fixationy",(len(labels),1),np.int16)
    hdf5_file.create_dataset("fixationx",(len(labels),1),np.int16)
    hdf5_file.create_dataset("retinatype",(len(labels),1),"S10")

    for i in xrange(len(vectors)):
        hdf5_file["vector"][i] = vectors[i]
        hdf5_file["label"][i] = labels[i]
        hdf5_file["framenum"][i] = framenums[i]
        hdf5_file["timestamp"][i] = timestamps[i]
        hdf5_file["fixationy"][i] = fixationY[i]
        hdf5_file["fixationx"][i] = fixationX[i]
        hdf5_file["retinatype"][i] = retinatypes[i]

    hdf5_file.close()

def loadCsv(filename, frames):
    metadata = pd.read_csv(filename,delimiter=" ",encoding="utf-8")
    currentframes = frames if frames else []
    print(metadata.shape)
    cols = metadata.columns
    if 'vector' not in cols and not currentframes:
        raise Exception('NoFrames')
    elif 'vector' not in cols:
        # load data into model here
        for i in xrange(len(currentFrames)):
            currentframe = currentframes[i]
            for column in cols:
                if hasattr(currentframe, column):
                    if column == 'framenum':
                        try:
                            val = int(metadata[column][i])
                        except ValueError:
                            raise Exception('InvalidFrameNum')
                    setattr(currentframe,column,metadata[column][i])
    else:
        # create new vector objects
        R = startRetina()
        count = 1
        listtest = list(metadata.groupby('vector').groups.items())
        print(listtest[0]['label'])
        for i in xrange(metadata.shape[0]):
            vector = np.asarray(metadata['vector'][i].split(","),
                dtype=np.float64)
            v = ImageVector(vector=vector,
                label=metadata['label'][i],
                fixationy=int(metadata['fixationy'][i]),
                fixationx=int(metadata['fixationx'][i]),
                retinatype=metadata['retinatype'][i])
            v.framenum = int(metadata['framenum'][i]) if 'framenum' in cols else count
            v._timestamp = metadata['timestamp'][i] if 'timestamp' in cols else None
            count += 1
            v.image = getBackProjection(R,v._vector,fix=(v.fixationy,v.fixationx))
            currentframes.append(v)
    return currentframes

def vectorFromCSV(row):
    vector = np.asarray(metadata['vector'][i].split(","),
        dtype=np.float64)
    v = ImageVector(vector=vector,
        label=metadata['label'][i],
        fixationy=int(metadata['fixationy'][i]),
        fixationx=int(metadata['fixationx'][i]),
        retinatype=metadata['retinatype'][i])
    v.framenum = int(metadata['framenum'][i]) if 'framenum' in cols else count
    v._timestamp = metadata['timestamp'][i] if 'timestamp' in cols else None
    count += 1
    v.image = getBackProjection(R,v._vector,fix=(v.fixationy,v.fixationx))


def saveCSV(exportname, frames):
    columns = ['_vector'] + dir(frames[0])
    df = pd.DataFrame([{fn: getattr(f,fn) for fn in columns} for f in frames])
    # exported file should be read with ';' delimiter ONLY
    df.to_csv(exportname,encoding='utf-8',sep=";") # compression='gzip'?
