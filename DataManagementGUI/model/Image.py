import sys
import os
import csv
import cv2
from os.path import join


class Image(object):

    filetypes = {
        'jpg': 'jpeg',
    }

    def __init__(self,image,name=None,type=None,filepath=None,colortype=None,parent=None,frameNum=None,label=None,fixationx=None,fixationy=None):
        self.image = image
        if filepath:
            self.name = filepath.split("/")[-1]
            self.type = filepath.split('.')[-1]
        self.filepath = filepath
        self.parent = parent
        self.framenum = frameNum
        self.colortype = colortype
        self.label = label
        self.fixationx = fixationx
        self.fixationy = fixationy

    def detachFromVideo(self):
        self.parent = None
        self.framenum = None

    def saveImageOnly(self,dir):
        print("Saving image")
        cv2.imwrite(join(dir,"frame%d.png" % self.framenum), self.image)
