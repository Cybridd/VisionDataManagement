import sys
import os
import csv
import cv2
import pandas as pd
import Image as im
from os.path import join


class Video(object):

    filetypes = {
        'mp4': 'mp4v',
        'avi': 'xvid'
    }

    def __init__(self,filepath,palette):
        self.name = filepath.split("/")[-1]
        self.filepath = filepath
        self.type = filepath.split('.')[-1]
        self.palette = palette
        self.frames = None # fill these on load?
        self.numFrames = None

    def getFrames(self):
        self.cap = cv2.VideoCapture(self.filepath)
        codec = cv2.VideoWriter_fourcc(*self.filetypes[self.type])
        self.cap.set(cv2.CAP_PROP_FOURCC, codec)
        numFrames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frames = [0] * numFrames
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frameNum = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.frames[frameNum - 1] = im.Image(frame,parent=self,frameNum=frameNum,name="frame"+str(frameNum))
            else:
                break
        print("Images are now in memory at self.frames. Save them to disk by calling a version of saveFrames")

    def saveFramesImageOnly(self):
        #out = cv2.VideoWriter()
        #cv2.imshow("test", self.frames[0].image)
        frames_dir = join(self.filepath.split("/")[0], "Frames")
        if not os.path.exists(frames_dir):
            os.makedirs(frames_dir)
        if self.frames:
            for frame in self.frames:
                if frame:
                    frame.saveImageOnly(frames_dir)
        else:
            print("Frames not yet captured from video. Try self.getFrames()")
