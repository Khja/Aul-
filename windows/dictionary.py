import PySide2
from PySide2 import QtWidgets, QtCore, QtGui

import main as mn
import model as md
import undo as ud
import const


class Add(QtWidgets.QDialog):
    def __init__(self, main, node = None):
        super(Add, self).__init__()
        self.ui = mn.loadUi('UI/dictionary/add_word.ui', self)
        self.main = main

        self.ui.buttonBox.accepted.connect(self.add)
        self.ui.buttonBox.rejected.connect(self.destroy)

        if node != None:
            self.node = node
            word, meaning, clas, gender, notes = self.node._data
            self.ui.setWindowTitle('Edit word')

            self.ui.word.setText(word)
            self.ui.meaning.insertPlainText(meaning)
            self.ui.gender.setText(gender)
            self.ui.notes.insertPlainText(notes)

            self.ui.buttonBox.accepted.connect(self.save)

        self.ui.show()

    def add(self):
        word = self.ui.word.text()
        meaning = self.ui.meaning.toPlainText()
        notes = self.ui.notes.toPlainText()
        gender = self.ui.gender.text()
        clas = self.ui.comboBox.currentText()

        node = md.NodeDict([word, meaning, clas, gender, notes], -1, self.main._dictModel, None)
        command = ud.AddWord(node, self.main)
        self.main._undoStack.push(command)
        self.destroy()

    def save(self):
        pass