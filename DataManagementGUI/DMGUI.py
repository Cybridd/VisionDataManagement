# -*- coding: utf-8 -*-
"""
Created on Thu Jun  21 15:17:11 2018

@author: Connor Fulton
"""

import sys
sys.path.append('E:\MScProject\RetinaVision\retinavision')

from Tkinter import *

class DataManagementGUI(Frame):

    def __init__(self,master):
        Frame.__init__(self,master)
        self.grid()
        #self.create_frames()

    #def create_frames(self):


root = Tk()
root.title("Vision Data Management")
root.geometry("1280x720")

app = DataManagementGUI(root)

root.mainloop()
