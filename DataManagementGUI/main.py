from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import design

class DMApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self,parent=None):
        super(DMApp,self).__init__(parent)
        self.setupUi(self)

def main():
    app = QtWidgets.QApplication(sys.argv)
    form = DMApp()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
