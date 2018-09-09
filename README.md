# VisionDataManagement
A desktop application built in Python for the management of data produced by the software retina being developed by the CVAS team at the University of Glasgow.

## Getting Started

### Requirements

  pandas
  opencv_python
  h5py
  numpy
  GPUtil
  PyQt5
  retinavision


### Installation
To install first clone the repository:

  git clone https://github.com/Cybridd/VisionDataManagement

You'll also need a copy of the RetinaVision repository as it cannot be installed automatically. Acquire collaborator credentials from the owner and clone it:

  git clone https://github.com/Pozimek/RetinaVision

Once you're on the virtual environment you wish to use, navigate to RetinaVision and install:

  pip install -e .

The rest of the dependencies will be installed automatically. To install, navigate to VisionDataManagement and call:

  python setup.py

Unfortunately, there is a bug in the version of PyQt5 used here that misplaces a configuration file.
To fix this, follow [these steps](https://github.com/pyqt/python-qt5/issues/2#issuecomment-305766548).






## Testing
To run the tests, navigate to the visiondatamanagement directory and call:

  python tests.py

To run only a specific test case, such as functional or performance, give the name:

  python tests.py AppTests


## Using the System
Navigate to visiondatamanagement and call:

  python main.py


This will run the program and open the GUI. From here most of the menus and controls are self-explanatory, but the tabs are:

  Webcam - try to connect to a webcam and view the live retinal backprojection and cortical image
  Main - large display of a single backprojection or other image for inspection
  Gallery - scroll through the data set, with multi-selection and deletion

Imagevector data files, video files and image files can all be imported and viewed, but only imagevector data can be exported.

If you encounter any problems during installation or use, please contact me at cfulton117@gmail.com and I'll try and assist.
