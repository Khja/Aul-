import main
import sys
from PySide2 import QtWidgets

if __name__ == '__main__':
    Aule = QtWidgets.QApplication(sys.argv)
    Aule.setQuitOnLastWindowClosed(False)
    window = main.MainWindow(Aule)
    sys.exit(Aule.exec_())
