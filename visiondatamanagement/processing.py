import sys
import os
import numpy as np
import pandas as pd
import cv2
import h5py
import re
import time
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

def getBackProjection(R,V,shape,fix):
    return R.backproject(V,shape,fix)

def getBackProjections(frame):
    R = startRetina()
    backshape = (720,1280,frame._vector.shape[-1])
    #R.prepare(backshape,fix=(frame.fixationy,frame.fixationx))
    return getBackProjection(R,frame._vector,backshape,fix=(frame.fixationy,frame.fixationx))

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

def loadhdf5(filename, frames, concurrbackproject=False):
    currentframes = frames if frames else []
    hdf5_open = h5py.File(filename, mode="r")
    R = startRetina()
    if R._cudaRetina:
        print("Using CUDA")
    count = 1
    if 'vector' in hdf5_open.keys():
        for i in xrange(len(hdf5_open['vector'])):
            if 'retinatype' in hdf5_open.keys():
                v = ImageVector(vector=hdf5_open['vector'][i],
                    label=hdf5_open['label'][i].tostring(),
                    fixationy=int(hdf5_open['fixationy'][i]),
                    fixationx=int(hdf5_open['fixationx'][i]),
                    retinatype=hdf5_open['retinatype'][i].tostring())
            else:
                v = ImageVector(vector=hdf5_open['vector'][i])
            v.framenum = int(hdf5_open['framenum'][i]) if 'framenum' in hdf5_open.keys() else count
            v._timestamp = hdf5_open['timestamp'][i].tostring() if 'timestamp' in hdf5_open.keys() else None
            count += 1
            currentframes.append(v)
        print("Vector shape: " + str(currentframes[0]._vector.shape))
        if concurrbackproject:
            print("Beginning backprojection using multiprocessing...")
            cpucount = mp.cpu_count() - 1
            pool = mp.Pool(cpucount)
            images = pool.map(getBackProjections, currentframes)
            for i in xrange(len(currentframes)):
                currentframes[i].image = images[i]
        else:
            backshape = (720,1280,currentframes[0]._vector.shape[-1])
            print("Backprojection shape: " + str(backshape))
            for frame in currentframes:
                start = time.time()
                frame.image = R.backproject(frame._vector,backshape,fix=(frame.fixationy,frame.fixationx))
                end = time.time()
                print("Backprojection took "+ str(end-start) + " seconds.")
    else:
        raise Exception('HDF5Format')
    return currentframes

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
    metadata = pd.read_csv(filename,delimiter=";",encoding="utf-8")#,index_col="framenum"
    currentframes = frames if frames else []
    print(metadata.shape)
    cols = metadata.columns
    print(cols)
    print(metadata.index.name)
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
        count = 1
        for i in xrange(metadata.shape[0]):
            print(metadata.shape[0])
            if metadata['vector'][i].startswith('['):
                print("We're here")
                vtemp = re.findall("\[(.*?)\]", metadata['vector'][i])
                print(vtemp[0])
                for j in xrange(len(vtemp)):
                    vtemp[j] = [x for x in vtemp[j].split(' ') if x]
                print(vtemp[0])
                vtemp = np.asarray([x for x in vtemp], dtype=np.float64)
                vector = np.asarray(vtemp,dtype=np.float64)
            else:
                vector = np.asarray(metadata['vector'][i].split(","),
                    dtype=np.float64)
            print("Fixation Y: " + str(metadata['fixationy'][i]))
            print("Fixation X: " + str(metadata['fixationx'][i]))
            v = ImageVector(vector=vector,
                label=metadata['label'][i],
                fixationy=int(metadata['fixationy'][i]),
                fixationx=int(metadata['fixationx'][i]),
                retinatype=metadata['retinatype'][i])
            v.framenum = int(metadata['framenum'][i]) if 'framenum' in cols else count
            v._timestamp = metadata['timestamp'][i] if 'timestamp' in cols else None
            count += 1
            currentframes.append(v)
        print("Vector shape: " + str(currentframes[0]._vector.shape))
        backshape = (720,1280,currentframes[0]._vector.shape[-1])
        print("Backprojection shape: " + str(backshape))
        R = startRetina()
        for frame in currentframes:
            start = time.time()
            fixation=(frame.fixationy,frame.fixationx)
            frame.image = R.backproject(frame._vector,backshape,fix=fixation)
            end = time.time()
            print("Backprojection took "+ str(end-start) + " seconds.")
        #cpucount = mp.cpu_count() - 1
        #pool = mp.Pool(cpucount)
        #images = pool.map(getBackProjections, currentframes)
        #for i in xrange(len(currentframes)):
        #    currentframes[i].image = images[i]
    return currentframes

def saveCSV(exportname, frames):
    columns = dir(frames[0])
    df = pd.DataFrame([{fn: getattr(f,fn) for fn in columns} for f in frames])
    vectorstrings = []
    for frame in frames:
        vs = ','.join(str(e) for e in frame._vector)
        vectorstrings.append(vs)
    df['vector'] = pd.Series(vectorstrings, index=df.index)
    df.rename(columns = {'_timestamp':'timestamp'}, inplace = True)
    # exported file should be read with ';' delimiter ONLY
    df.to_csv(exportname,encoding='utf-8',sep=";") # compression='gzip'?

def loadPickle(filename):
    return utils.loadPickle(filename)
