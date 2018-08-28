import unittest
import sys
import os
import main
import csv
import timeit
import gc
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
#        testframes = ip.loadhdf5(os.path.join("testdata","testfilesmall.h5"),None)
#        print("Saving HDF5 test file unchanged...")
#        ip.saveHDF5(os.path.join("testdata","testfileoutput.h5"),testframes)

        # differences between the files can be observed using h5diff, a tool of the HDF5
        # package from the command line. Attempts to find a programmatic method of comparing
        # files that isn't extremely time consuming have been unsuccessful, but I will
        # continute looking until delivery.

#    def test_csv_consistency(self):
#        print("Loading CSV test file...")
#        testframes = ip.loadCsv(os.path.join("testdata","extrasmalltestfile.csv"),None)
#        print("Saving CSV test file unchanged...")
#        ip.saveCSV(os.path.join("testdata","csvconsistencyoutput.csv"),testframes)


        # differences between the files must be observed manually at the moment. Attempts
        # to find a programmatic method of comparing files that isn't extremely time consuming
        # have been unsuccessful, but I will continute looking until delivery.

#        with open(os.path.join("testdata","new.csv"), 'r') as filein, open(os.path.join("testdata","newoutput.csv"), 'r') as fileout:
#            f1 = filein.readlines()
#            f2 = fileout.readlines()
#
#        with open(os.path.join("testdata","diff.csv"), 'w') as diffFile:
#            for line in f2:
#                if line not in f1:
#                    diffFile.write(line)

#        filein = frozenset(tuple(row) for row in csv.reader(open(os.path.join("testdata","new.csv"), 'r'), delimiter=' '))
#        fileout = frozenset(tuple(row) for row in csv.reader(open(os.path.join("testdata","newoutput.csv"), 'r'), delimiter=' '))

#        added = [" ".join(row) for row in fileout - filein]
#        removed = [" ".join(row) for row in filein - fileout]
#        print("Differences between the input and output files have been written to diff.csv")

    def test_prohibited_file_types(self):
        # reference to valid hdf5 file is stored
        print("Opening HDF5 test file...")
        filename = os.path.join("testdata","testfile.h5")
        self.form.openFile(filename)
        self.assertEquals(self.form.currentFile, filename, 'Valid file reference not stored')
        print('Valid file reference stored')

        self.form.currentFile = None # manually delete to avoid dependency on closeFile()

        # reference to invalid doc file is not stored
        print("Opening invalid file format (.doc)...")
        filename = os.path.join("testdata","testfile.doc")
        self.form.openFile(filename)
        self.assertIsNone(self.form.currentFile, 'Invalid file reference stored')
        print('Invalid file reference not stored')

    def test_close_file(self):
        print("Closing test file...")
        filename = os.path.join("testdata","testfile.h5")
        self.form.openFile(filename)
        self.form.closeFile()
        self.assertIsNone(self.form.currentFile, 'File not closed, reference still exists')
        print('File successfully closed')

    def test_hdf5_format_restricted(self):
        print("Loading HDF5 test file with no imagevectors...")
        self.assertRaises(Exception,ip.loadhdf5,os.path.join("testdata","invalidtestfile.h5"))
        print("Exception raised on loading of hdf5 file with no imagevectors")

    def test_HDF5_file_with_partial_metadata_rejected(self):
        print("Loading HDF5 file with incomplete metadata...")
        self.assertRaises(Exception,ip.loadhdf5,os.path.join("testdata","partialmetadatafile.h5"),None)
        print("Exception raised on loading of HDF5 file with only partial metadata")

    def test_HDF5_file_with_unequal_dataset_lengths_rejected(self):
        print("Loading HDF5 file with unequal length data sets...")
        self.assertRaises(Exception,ip.loadhdf5,os.path.join("testdata","unequallengthdatafile.h5"),None)
        print("Exception raised on loading of HDF5 file with unequal dataset lengths")

    def test_CSV_file_with_partial_metadata_rejected(self):
        print("Loading CSV file with incomplete metadata...")
        self.assertRaises(Exception,ip.loadCsv,os.path.join("testdata","partialmetadatafile.csv"),None)
        print("Exception raised on loading of CSV file with only partial metadata")

    def test_CSV_file_with_unequal_dataset_lengths_rejected(self):
        print("Loading CSV file with unequal length data sets...")
        self.assertRaises(Exception,ip.loadCsv,os.path.join("testdata","unequallengthdatafile.csv"),None)
        print("Exception raised on loading of CSV file with unequal dataset lengths")

    def test_loading_metadata_before_imagedata_prohibited(self):
        print("Loading CSV test file before vectors...")
        self.assertRaises(Exception,ip.loadCsv,os.path.join("testdata","novectorstestfile.csv"),None)
        print("Exception raised on loading metadata before vectors")

    def test_metadata_value_type_restricted(self):
        # currently the only metadata type that allows editing is the label,
        # which can be anything. Wider editing possibilities may be added
        pass

    def tearDown(self):
        pass

class PerformanceTests(TestCase):

    # Results are larger than typical for normal use, but more accurate, as timeit
    # module disables garbage collection.

    # Loading a HDF5 file. Generation of backprojections is included in this test,
    # as this is always the procedure. This requires the majority of the execution
    # time.
    def test_hdf5_loading_performance(self):
        # key: sm - small file, lg - large file, nc - nonconcurrent, c - nonconcurrent
        sm_nc_times,sm_c_times,lg_nc_times,lg_c_times = (0 for i in range(4))
        setup = "import processing as ip; import os"
        runs = 100

        sm_nc_times = timeit.timeit('ip.loadhdf5(os.path.join("testdata","testfilesmall.h5"),None)',setup=setup,number=runs)
        print("Average time to load small hdf5 non-concurrently ("+str(runs)+" runs): " + str(sm_nc_times/float(runs)) + " seconds")

        gc.collect()

    #    sm_c_times = timeit.timeit('ip.loadhdf5(os.path.join("testdata","testfilesmall.h5"),None,concurrbackproject=True)',setup=setup,number=runs)
    #    print("Average time to load small hdf5 concurrently ("+str(runs)+" runs): " + str(sm_c_times/float(runs)) + " seconds")

        gc.collect()

        lg_nc_times = timeit.timeit('ip.loadhdf5(os.path.join("testdata","testfile.h5"),None)',setup=setup,number=runs)
        print("Average time to load large hdf5 non-concurrently ("+str(runs)+" runs): " + str(lg_nc_times/float(runs)) + " seconds")

        gc.collect()

    #    lg_c_times = timeit.timeit('ip.loadhdf5(os.path.join("testdata","testfile.h5"),None,concurrbackproject=True)',setup=setup,number=runs)
    #    print("Average time to load large hdf5 concurrently ("+str(runs)+" runs): " + str(lg_c_times/float(runs)) + " seconds")

        gc.collect()
        # 1000 50k vectors serial - 141.82s
        # 1000 50k vectors concurrent - 2108.56s

    # FEED THIS SHIT THROUGH THE CORTEX AS A SANITY CHECK

if __name__ == '__main__':
    unittest.main(exit=False)
