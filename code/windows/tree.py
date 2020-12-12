import PySide2
from PySide2 import QtWidgets, QtCore, QtGui

import main as mn
import model as md
import undo as ud
import const

class Add(QtWidgets.QDialog):
    def __init__(self, main, root=None):
        super(Add, self).__init__()
        self.ui = mn.loadUi('UI/tree/add_object.ui')
        self.main = main

        self.ui.buttonBox.accepted.connect(self.add)
        self.ui.buttonBox.rejected.connect(self.destroy)

        self.parent = root # Parent of new object

        self.ui.show()

    def add(self):
        # Name
        name = self.ui.name.text()

        """ if len(name) == 0:
            n = self.main.uc_object
            if n == 0:
                n = ''
            self.main.uc_object += 1

            name = f'New Object {n}' """

        # Type
        obj_type = self.ui.type.currentText()

        data = {
            '_name': name,
            '_type': obj_type,
            '_notes': ''
        }

        # Add
        node = md.Node(
            data,
            self.main._treeModel,
            None,
            1
        )

        command = ud.AddToTree(node, self.parent, self.main)
        self.main._undoStack.push(command)

        if self.parent != None:
            self.main.ui.treeView.expand(self.parent)


class Edit(const.EditDialog):
    def __init__(self, main, node):
        super().__init__(main, node)
        self.ui = mn.loadUi('UI/tree/edit_object.ui', self)

        self.ui.setWindowTitle(f'Edit Folder')

        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.buttonBox.rejected.connect(self.destroy)

        # Display info
        self.setup()
        index = self.ui.type.findText(self.node._notes, QtCore.Qt.MatchFixedString)
        self.ui.type.setCurrentIndex(index)

        # Disable comboBox
        self.ui.type.setEnabled(False)

        self.ui.show()

    def save(self):
        # Name
        name = self.ui.name.text()
        # Type
        node_type = self.ui.type.currentText()
        # Notes
        notes = self.ui.notes.toPlainText()

        old_data, new_data = self.data()

        self.push(old_data, new_data, self.node)
