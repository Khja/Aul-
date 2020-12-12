import sys
import PySide2
from PySide2 import QtWidgets, QtCore, QtGui

import undo as ud

class EditDialog(QtWidgets.QDialog):
    def __init__(self, main, node):
        super(EditDialog, self).__init__()

        self.main = main
        self.node = node

    def setup(self):
        self.ui.name.setText(self.node._name)
        self.ui.notes.insertPlainText(self.node._notes)

    def data(self):
        old_data = {
            '_name': self.node._name,
            '_notes': self.node._notes
        }

        new_data = {
            '_name': self.ui.name.text(),
            '_notes': self.ui.notes.toPlainText()
        }
        return old_data, new_data

    def push(self, old_data, new_data, node):
        command = ud.EditNode(old_data, new_data, node, self.main)
        self.main._undoStack.push(command)