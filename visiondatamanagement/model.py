"""
Created on 08/07/2018 14:31

Model for the vision data management system.

@author: Connor Fulton
"""

import sys
import os
import csv
import cv2
from os.path import join

class ImageVector(object):
    """Represents an imagevector and its associated metadata"""
    def __init__(self,vector,id=None,framenum=None,timestamp=None,label=None,fixationy=None,fixationx=None,retinatype=None,vectortype=None):
        self._vector = vector
        self.id = id
        self.image = None # backprojected image for display
        self.framenum = framenum
        self._timestamp = timestamp
        self.label = label
        self.fixationy = fixationy
        self.fixationx = fixationx
        self.retinatype = retinatype
        self.vectortype = vectortype

    def __dir__(self):
        return ['id','framenum','_timestamp','label','fixationy','fixationx','retinatype','vectortype']

class Image(object):
    """Represents an image file and its associated metadata"""
    def __init__(self,image=None,name=None,filepath=None,colortype=None,parent=None,framenum=None,label=None):
        self.vector = None
        self.type = None
        self.image = image
        self.name = name
        if filepath:
            self.type = filepath.split('.')[-1]
            if not name:
                self.name = filepath.split("/")[-1]
        self.filepath = filepath
        self.parent = parent
        self.framenum = framenum
        self.colortype = colortype
        self.label = label

    def saveImageOnly(self,dir):
        """Save the image back to file if required"""
        print("Saving image")
        cv2.imwrite(join(dir,"frame%d.png" % self.framenum), self.image)

    def __dir__(self):
        return ['name','type','framenum','colortype','label']

class Video(object):
    """Represents a video file, its metadata and individual frames if generated"""
    filetypes = {
        'mp4': 'mp4v',
        'avi': 'xvid'
    }

    def __init__(self,filepath,colortype):
        self.name = filepath.split("/")[-1]
        self.filepath = filepath
        self.type = filepath.split('.')[-1]
        self.colortype = colortype
        self.frames = None # list of Images, filled upon user request
        self.numFrames = None

    def getFrames(self):
        """Use OpenCV to split the video file into frames and capture them"""
        self.cap = cv2.VideoCapture(self.filepath)
        codec = cv2.VideoWriter_fourcc(*self.filetypes[self.type])
        self.cap.set(cv2.CAP_PROP_FOURCC, codec)
        self.numFrames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frames = [0] * self.numFrames
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                framenum = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.frames[framenum - 1] = Image(frame,parent=self,framenum=framenum,name="frame"+str(framenum))
            else:
                break
        print("Images are now in memory at self.frames. Save them to disk by calling a version of saveFrames")
        return self.frames

    def saveFramesImageOnly(self):
        """Saves the images back to file if required"""
        frames_dir = join(self.filepath.split("/")[0], "Frames")
        if not os.path.exists(frames_dir):
            os.makedirs(frames_dir)
        if self.frames:
            for frame in self.frames:
                if frame:
                    frame.saveImageOnly(frames_dir)
        else:
            print("Frames not yet captured from video. Try self.getFrames()")
