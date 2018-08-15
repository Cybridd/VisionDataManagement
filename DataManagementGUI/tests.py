import unittest
import sys
import os
import main
from unittest import TestCase


class InputTests(TestCase):

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    def setUp(self):
        app = QApplication(sys.argv)
        form = DMApp()

    def test_hdf5_consistency(self):
        pass

    def test_prohibited_file_types(self):
        pass # assertRaises

    def test_hdf5_format_restricted(self):
        pass # assertRaises

    def test_loading_metadata_before_imagedata_prohibited(self):
        pass # assertRaises

    def test_metadata_value_type_restricted(self):
        pass # not yet implemented

    def tearDown(self):
        form.closeApp()

if __name__ == '__main__':
    unittest.main()
