"""
Created on 7/18/2018 11:20

Processing functions for the VDM application. The i/o functions are used exclusively
by worker threads, the others are used by this class and by the controller.

@author: Connor Fulton
"""

import sys
import os
from functools import partial
from os.path import join
import re
import time
import multiprocessing as mp
import numpy as np
import pandas as pd
import cv2
import h5py
from PyQt5 import QtGui, QtCore
from QtGui import QImage, QPixmap
from QtCore import Qt
from model import Image, ImageVector
from retinavision.retina import Retina
from retinavision.cortex import Cortex
from retinavision import datadir, utils

def prepareLiveRetina(cap):
    """Performs extra preparation steps for using the retina with a webcam

    Parameters
    ----------
    cap : VideoCapture object capturing the video feed
    """

    retina = startRetina()
    ret, frame = cap.read()
    # fixed fixation at centre of video feed
    x = frame.shape[1]/2
    y = frame.shape[0]/2
    fixation = (y,x)
    retina.prepare(frame.shape, fixation)
    return retina, fixation

def startRetina():
    """Instantiates Retina object and loads necessary files"""
    retina = Retina()
    retina.loadLoc(join(datadir, "retinas", "ret50k_loc.pkl"))
    retina.loadCoeff(join(datadir, "retinas", "ret50k_coeff.pkl"))
    return retina

def getBackProjection(R,V,shape,fix):
    """Proxy function for Retina.backproject()"""
    return R.backproject(V,shape,fix)

def getBackProjections(frame, R):
    """Gets backprojection given only an image. Similar to a Python partial function"""
    #R = startRetina()
    backshape = (720,1280,frame._vector.shape[-1])
    return getBackProjection(R,frame._vector,backshape,fix=(frame.fixationy,frame.fixationx))

def createCortex():
    """Instantiates Cortex object and loads necessary files"""
    cortex = Cortex()
    lp = join(datadir, "cortices", "50k_Lloc_tight.pkl")
    rp = join(datadir, "cortices", "50k_Rloc_tight.pkl")
    cortex.loadLocs(lp, rp)
    cortex.loadCoeffs(join(datadir, "cortices", "50k_Lcoeff_tight.pkl"), join(datadir, "cortices", "50k_Rcoeff_tight.pkl"))
    return cortex

def convertToPixmap(frame, x, y, BGR=False):
    """Converts images into QPixmap ojbects so they can be understood by UI elements

    Parameters
    ----------
    frame : image to be displayed
    x : width needed
    y : height needed
    BGR : boolean if colour space is BGR
    """

    if frame.shape[-1] == 3:
        # TODO: reduce precariousness of this color space change
        if BGR:
            frame = cv2.cvtColor(frame,cv2.cv2.COLOR_BGR2RGB)
        format = QImage.Format_RGB888
    # image is grayscale (1 channel)
    else:
        format = QImage.Format_Grayscale8
    # convert first to QImage...
    converttoQtFormat = QImage(frame.data,frame.shape[1],frame.shape[0],format)
    # ...scale result...
    pic = converttoQtFormat.scaled(x,y,Qt.KeepAspectRatio)
    # ...and then convert to QPixmap
    pixmap = QPixmap.fromImage(pic)
    return pixmap

def createImagesFromFolder(currentDir):
    """Scans a given directory and generates Image objects for all images found

    Parameters
    ----------
    currentDir : selected directory for search
    """

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
    """Loads a HDF5 data file and generates ImageVector objects for each record

    Parameters
    ----------
    filename : specified source name
    frames : existing frames in system (should probably pass something lighter)
    concurrbackproject : boolean for using multiprocessing to generate backprojections
    """

    currentframes = frames if frames else []
    hdf5_open = h5py.File(filename, mode="r")
    R = startRetina()
    # inform user if cudaRetina is enabled
    if R._cudaRetina:
        print("Using CUDA")
    count = 1
    if 'vector' in hdf5_open.keys():
        for i in xrange(len(hdf5_open['vector'])):
            try:
                # if metadata is available, try and load it
                if 'retinatype' in hdf5_open.keys():
                    v = ImageVector(vector=hdf5_open['vector'][i],
                        label=hdf5_open['label'][i].tostring(),
                        fixationy=int(hdf5_open['fixationy'][i]),
                        fixationx=int(hdf5_open['fixationx'][i]),
                        retinatype=hdf5_open['retinatype'][i].tostring())
                # if not, load just the imagevectors
                else:
                    v = ImageVector(vector=hdf5_open['vector'][i])
                # load these metadata items if available, else an alternative
                v.framenum = int(hdf5_open['framenum'][i]) if 'framenum' in hdf5_open.keys() else count
                v._timestamp = hdf5_open['timestamp'][i].tostring() if 'timestamp' in hdf5_open.keys() else None
                v.vectortype = hdf5_open['vectortype'][i].tostring() if 'vectortype' in hdf5_open.keys() else None
            except:
                raise Exception('HDF5Format')
            count += 1
            currentframes.append(v)
        print("Vector shape: " + str(currentframes[0]._vector.shape))
        # use multiprocessing for generating backprojections
        if concurrbackproject:
            print("Beginning backprojection using multiprocessing...")
            cpucount = mp.cpu_count() - 1
            pool = mp.Pool(cpucount)
            partialgetBackProject = partial(getBackProjections, R=startRetina())
            images = pool.map(partialgetBackProject, currentframes)
            for i in xrange(len(currentframes)):
                currentframes[i].image = images[i]
        # generate backprojections in this thread
        else:
            backshape = (720,1280,currentframes[0]._vector.shape[-1])
            print("Backprojection shape: " + str(backshape))
            for frame in currentframes:
                start = time.time()
                frame.image = R.backproject(frame._vector,backshape,fix=(frame.fixationy,frame.fixationx))
                #encode_param = [int(cv2.IMWRITE_PNG_COMPRESSION), 3]
                #result, frame.image = cv2.imencode('.png',im,encode_param)
                end = time.time()
                # inform the user of current performance for diagnostics
                print("Backprojection took "+ str(end-start) + " seconds.")
    else:
        raise Exception('HDF5Format')
    return currentframes

def saveHDF5(exportname, frames):
    """Creates a h5py File object and stores the current frames within it

    Parameters
    ----------
    exportname : specified name (and location) of output file
    frames : list of frames to be stored
    """

    vectors, labels, framenums, timestamps, fixationY, fixationX, retinatypes, vectortypes = ([] for i in range(8))
    hdf5_file = h5py.File(exportname, mode='w')
    currentframe = None
    # extract attributes into separate lists
    for i in xrange(len(frames)):
        currentframe = frames[i]
        vectors.append(currentframe._vector)
        labels.append(currentframe.label)
        framenums.append(currentframe.framenum)
        timestamps.append(currentframe._timestamp)
        fixationY.append(currentframe.fixationy)
        fixationX.append(currentframe.fixationx)
        retinatypes.append(currentframe.retinatype)
        vectortypes.append(currentframe.vectortype)

    # create datasets in new file with appropriate data types
    hdf5_file.create_dataset("vector",(len(vectors),len(currentframe._vector),currentframe._vector.shape[-1]),np.float64)
    hdf5_file.create_dataset("label",(len(labels),1),"S20")
    hdf5_file.create_dataset("framenum",(len(labels),1),np.int16)
    hdf5_file.create_dataset("timestamp",(len(labels),1),"S11")
    hdf5_file.create_dataset("fixationy",(len(labels),1),np.int16)
    hdf5_file.create_dataset("fixationx",(len(labels),1),np.int16)
    hdf5_file.create_dataset("retinatype",(len(labels),1),"S10")
    hdf5_file.create_dataset("vectortype",(len(labels),1),"S10")

    # store data in new datasets
    for i in xrange(len(vectors)):
        hdf5_file["vector"][i] = vectors[i]
        hdf5_file["label"][i] = labels[i]
        hdf5_file["framenum"][i] = framenums[i]
        hdf5_file["timestamp"][i] = timestamps[i]
        hdf5_file["fixationy"][i] = fixationY[i]
        hdf5_file["fixationx"][i] = fixationX[i]
        hdf5_file["retinatype"][i] = retinatypes[i]
        hdf5_file["vectortype"][i] = vectortypes[i]

    hdf5_file.close()

def loadCsv(filename, frames, concurrbackproject=False):
    """Loads a CSV data file and  either generates ImageVector objects for each
    record, or adds metadata to existing frames

    Parameters
    ----------
    filename : specified source name
    frames : existing frames in system (should probably pass something lighter)
    concurrbackproject : boolean for using multiprocessing to generate backprojections
    """

    metadata = pd.read_csv(filename,delimiter=";",encoding="utf-8")#,index_col="framenum"
    currentframes = frames if frames else []
    cols = metadata.columns
    print("Columns found: " + str(cols))
    if 'vector' not in cols and not currentframes:
        raise Exception('NoFrames')
    elif 'vector' not in cols:
        # load data into existing model here
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
            # interpreting the imagevector column
            if metadata['vector'][i].startswith('['):
                # if it's a multi-channel Imagevector, break around '[]'
                vtemp = re.findall("\[(.*?)\]", metadata['vector'][i])
                # break resulting strings again into string numbers
                for j in xrange(len(vtemp)):
                    vtemp[j] = [x for x in vtemp[j].split(' ') if x]
                # convert string number lists into floating-point arrays
                vtemp = np.asarray([x for x in vtemp], dtype=np.float64)
                # convert list of lists into an array
                vector = np.asarray(vtemp,dtype=np.float64)
            else:
                # if it's a single-channel vector, just break around commas
                vector = np.asarray(metadata['vector'][i].split(","),
                    dtype=np.float64)
            try:
                v = ImageVector(vector=vector,
                    label=metadata['label'][i],
                    fixationy=int(metadata['fixationy'][i]),
                    fixationx=int(metadata['fixationx'][i]),
                    retinatype=metadata['retinatype'][i])
                v.framenum = int(metadata['framenum'][i]) if 'framenum' in cols else count
                v._timestamp = metadata['timestamp'][i] if 'timestamp' in cols else None
                v.vectortype = hdf5_open['vectortype'][i] if 'vectortype' in cols else None
            except:
                raise Exception('CSVFormat')
            count += 1
            currentframes.append(v)
        # Show user resulting array's shape for diagnostics
        print("Vector shape: " + str(currentframes[0]._vector.shape))
        # use multiprocessing for generating backprojections
        if concurrbackproject:
            print("Beginning backprojection using multiprocessing...")
            cpucount = mp.cpu_count() - 1
            pool = mp.Pool(cpucount)
            images = pool.map(getBackProjections, currentframes)
            for i in xrange(len(currentframes)):
                currentframes[i].image = images[i]
        # generate backprojections in this thread
        else:
            backshape = (720,1280,currentframes[0]._vector.shape[-1])
            print("Backprojection shape: " + str(backshape))
            R = startRetina()
            for frame in currentframes:
                start = time.time()
                fixation=(frame.fixationy,frame.fixationx)
                frame.image = R.backproject(frame._vector,backshape,fix=fixation)
                end = time.time()
                # inform the user of current performance for diagnostics
                print("Backprojection took "+ str(end-start) + " seconds.")
    return currentframes

def saveCSV(exportname, frames):
    """Creates a dataframe and stores the current frames within it, before
    converting to a CSV file

    Parameters
    ----------
    exportname : specified name (and location) of output file
    frames : list of frames to be stored
    """

    # get attribute names
    columns = dir(frames[0])
    # create a dataframe with columns named after attributes and store values
    df = pd.DataFrame([{fn: getattr(f,fn) for fn in columns} for f in frames])
    vectorstrings = []
    for frame in frames:
        # convert the imagevector into a string suitable for storage in CSV
        vs = ','.join(str(e) for e in frame._vector)
        vectorstrings.append(vs)
    df['vector'] = pd.Series(vectorstrings, index=df.index)
    df.rename(columns = {'_timestamp':'timestamp'}, inplace = True)
    # exported file should be read with ';' delimiter ONLY
    df.to_csv(exportname,encoding='utf-8',sep=";") # compression='gzip'?

def loadPickle(filename):
    return utils.loadPickle(filename)
