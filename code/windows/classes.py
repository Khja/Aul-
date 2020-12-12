import PySide2
from PySide2 import QtWidgets, QtCore, QtGui

import main as mn
import model as md
import undo as ud
import const

class Edit(const.EditDialog):
    def __init__(self, main, node):
        super().__init__(main, node)
        self.ui = mn.loadUi('UI/classes/edit.ui', self)
        self.setup()
        self.ui.genders.setText(self.node._genders)

        self.ui.buttonBox.accepted.connect(self.save)

        self.ui.show()

    def save(self):
        old_data, new_data = self.data()
        old_data['_genders'] = self.node._genders
        new_data['_genders'] = self.ui.genders.text()

        self.push(old_data, new_data, self.node)
