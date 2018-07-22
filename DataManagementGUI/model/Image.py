import sys
import os
import csv
import cv2
from os.path import join


class Image(object):

    filetypes = {
        'jpg': 'jpeg',
    }

    def __init__(self,image,name=None,type=None,filepath=None,palette=None,parent=None,frameNum=None,label=None,fixation=None):
        self.image = image
        if filepath:
            self.name = filepath.split("/")[-1]
            self.type = fileName.split('.')[-1]
        self.filepath = filepath
        self.parent = parent
        self.frameNum = frameNum
        self.palette = palette
        self.label = label
        self.fixation = fixation

    def detachFromVideo(self):
        self.parent = None
        self.frameNum = None

    def saveImageOnly(self,dir):
        print("Saving image")
        cv2.imwrite(join(dir,"frame%d.png" % self.frameNum), self.image)
