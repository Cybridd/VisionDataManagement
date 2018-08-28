import unittest
import sys
import os
import main
import csv
from main import DMApp
from PyQt5 import QtCore, QtGui, QtWidgets
from QtCore import *
from QtGui import *
from QtWidgets import *
import processing as ip
from retinavision.retina import Retina
import cv2
from unittest import TestCase


class AppTests(TestCase):

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    def setUp(self):
        self.app = QApplication(sys.argv)
        self.form = DMApp()

#    def test_hdf5_consistency(self):
#        print("Loading HDF5 test file...")
#        testframes = ip.loadhdf5(os.path.join("testdata","testfile.h5"),None)
#        print("Saving HDF5 test file unchanged...")
#        ip.saveHDF5(os.path.join("testfileoutput.h5"),testframes)
#
#        # differences between the files can be observed using h5diff, a tool of the HDF5
#        # package from the command line. But I will try and find a way to automate it here

    def test_csv_consistency(self):
        print("Loading CSV test file...")
        testframes = ip.loadCsv(os.path.join("testdata","new.csv"),None)
        print("Saving CSV test file unchanged...")
        ip.saveCSV(os.path.join("testdata","newoutput.csv"),testframes)

#        with open(os.path.join("testdata","new.csv"), 'r') as filein, open(os.path.join("testdata","newoutput.csv"), 'r') as fileout:
#            f1 = filein.readlines()
#            f2 = fileout.readlines()
#
#        with open(os.path.join("testdata","diff.csv"), 'w') as diffFile:
#            for line in f2:
#                if line not in f1:
#                    diffFile.write(line)

        filein = frozenset(tuple(row) for row in csv.reader(open(os.path.join("testdata","new.csv"), 'r'), delimiter=' '))
        fileout = frozenset(tuple(row) for row in csv.reader(open(os.path.join("testdata","newoutput.csv"), 'r'), delimiter=' '))

        added = [" ".join(row) for row in fileout - filein]
        removed = [" ".join(row) for row in filein - fileout]
        print("Differences between the input and output files have been written to diff.csv")

#    def test_prohibited_file_types(self):
#        # reference to valid hdf5 file is stored
#        print("Opening HDF5 test file...")
#        filename = os.path.join("testdata","testfile.h5")
#        self.form.openFile(filename)
#        self.assertEquals(self.form.currentFile, filename, 'Valid file reference not stored')
#        print('Valid file reference stored')
#
#        self.form.currentFile = None # manually delete to avoid dependency on closeFile()
#
#        # reference to invalid doc file is not stored
#        print("Opening invalid file format (.doc)...")
#        filename = os.path.join("testdata","testfile.doc")
#        self.form.openFile(filename)
#        self.assertIsNone(self.form.currentFile, 'Invalid file reference stored')
#        print('Invalid file reference not stored')
#
#    def test_close_file(self):
#        print("Closing test file...")
#        filename = os.path.join("testdata","testfile.h5")
#        self.form.openFile(filename)
#        self.form.closeFile()
#        self.assertIsNone(self.form.currentFile, 'File not closed, reference still exists')
#        print('File successfully closed')
#
#    def test_hdf5_format_restricted(self):
#        print("Loading invalid HDF5 test file...")
#        self.assertRaises(Exception,ip.loadhdf5,os.path.join("testdata","invalidtestfile.h5"))
#        print("Exception raised on loading of invalid hdf5 file")
#
#
#    def test_loading_metadata_before_imagedata_prohibited(self):
#        print("Loading CSV test file before vectors...")
#        self.assertRaises(Exception,ip.loadCsv,os.path.join("testdata","novectorstestfile.csv"))
#        print("Exception raised on loading metadata before vectors")
#
#    def test_metadata_value_type_restricted(self):
#        # currently the only metadata type that allows editing is the label,
#        # which can be anything. Wider editing possibilities may be added
#        pass

    def tearDown(self):
        pass

class PerformanceTests(TestCase):

    def test_hdf5_loading_performance(self):
        pass
        # 1000 50k vectors serial - 141.82s
        # 1000 50k vectors concurrent - 2108.56s



if __name__ == '__main__':
    unittest.main(exit=False)
