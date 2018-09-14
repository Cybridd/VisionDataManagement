import os
import sys
from setuptools import setup
from setuptools.command.install import install


class PostInstallCommand(install):
    """Tasks to perform after installation"""
    def run(self):
        if os.name == 'nt':
            try:
                sys.path.index(os.path.join(os.environ["ProgramFiles"],"NVIDIA CORPORATION","NVSMI"))
            except ValueError:
                sys.path.append(os.path.join(os.environ["ProgramFiles"],"NVIDIA CORPORATION","NVSMI"))
        install.run(self)
        
def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

setup(
    name="visiondatamanagement",
    version="0.1",
    author="Connor Fulton",
    author_email="cfulton117@gmail.com",
    description="A tool for the management of data produced by the RetinaVision system.",
    packages=["visiondatamanagement"],
    classifiers=(
        "Programming Language :: Python :: 2",
        "Operating System :: OS Independent",
    ),
    long_description=read('README.md'),
    install_requires=[read(os.path.join('visiondatamanagement','requirements.txt'))],
    dependency_links=[
    "git+ssh://git@github.com/Pozimek/RetinaVision@1693fbcaad0813a0bc8937b6dd4288cbdd273e4c#egg=retinavision-0.9",
    "git://github.com/pyqt/python-qt5#egg=python-qt5",
    ],
    cmdclass={
        'install': PostInstallCommand,
    },
)
