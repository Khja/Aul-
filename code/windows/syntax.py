import PySide2
from PySide2 import QtWidgets, QtCore, QtGui

import model as md
import undo as ud
import const

# Why does this even exist?

class Edit(const.EditDialog):
    def __init__(self, main, node):
        super().__init__(main, node)
        uic.loadUi('UI/syntax/edit.ui', self)
        self.buttonBox.accepted.connect(self.save)
        self.show()

    def save(self):
        old_data, new_data = self.data()
        self.push(old_data, new_data, self.node)
