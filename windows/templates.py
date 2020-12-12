import PySide2
from PySide2 import QtWidgets, QtCore, QtGui

import main as mn
import model as md
import undo as ud

class ManageTemplates(QtWidgets.QDialog):
    def __init__(self, parent):
        super(ManageTemplates, self).__init__()
        self.ui = mn.loadUi('UI/template/manage4.ui', self)
        self.main = parent

        self._model = parent._templateModel
        self.ui.listView.setModel(self._model)

        # Connect the add button to the add method
        self.ui.addBtn.clicked.connect(self.add)
        self.ui.buttonBox.accepted.connect(self.destroy)
        self.ui.finishBtn.clicked.connect(self.save)
        self.ui.listView.doubleClicked.connect(self.edit)

        self.ui.edit.hide()
        # Table Model and View
        self.ui.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.ui.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        # Update after editing
        self.ui.columns.editingFinished.connect(self.updateTable)
        self.ui.rows.editingFinished.connect(self.updateTable)

        self.ui.show()

    def add(self):
        self.ui.edit.show()
        self.ui.columns.setText('')
        self.ui.rows.setText('')
        self.ui.name.setText('')
        self.ui.notes.clear()
        self.updateTable()

    def edit(self):
        '''Shows a window for editing the selected table template'''
        # to ensure there are no other windows open
        selected_indices = self.ui.listView.selectionModel().selectedIndexes()

            # if there is a selected template
        if len(selected_indices) > 0:
            index = selected_indices[0] # The index of the selected template
            template = self.main._templateModel.itemAt(index)
            self.template = template
            self.ui.edit.show()

            # Display information
            self.ui.columns.setText(self.template['_columns'])
            self.ui.rows.setText(self.template['_rows'])
            self.ui.name.setText(self.template['_name'])
            self.ui.notes.clear()
            self.ui.notes.insertPlainText(self.template['_notes'])
            self.updateTable()

    def updateTable(self):
        # Update columns
        columns = self.ui.columns.text().split(', ')
        self.ui.table.setColumnCount(len(columns))
        self.ui.table.setHorizontalHeaderLabels(columns)
        # Update rows
        rows = self.ui.rows.text().split(', ')
        self.ui.table.setRowCount(len(rows))
        self.ui.table.setVerticalHeaderLabels(rows)

        #self.u = (columns, rows)

    def save(self):
        if self.template != None:
            self.template['_name'] = self.ui.name.text()
            self.template['_columns'] = self.ui.columns.text()
            self.template['_rows'] = self.ui.rows.text()
            self.template['_notes'] = self.ui.notes.toPlainText()
            # Update database
            self.main.cursor.execute(
                'UPDATE templates SET _name = ?, _rows = ?, _columns = ?, _notes = ? WHERE _id = ?',
                (
                    self.template['_name'],
                    self.template['_rows'],
                    self.template['_columns'],
                    self.template['_notes'],
                    self.template['_id']
                )
            )
            self.main.conn.commit()
        else:
            self.addNew()
        self.ui.edit.hide()

    def addNew(self):
        self.updateTable()

        if len(self.ui.columns.text() + self.ui.rows.text()) > 0 or len(self.ui.name.text()) > 0:

            if len(self.ui.name.text()) > 0:
                name = self.ui.name.text()

            else:
                name = 'New Template'

            # before we create the template we must check if the name is not already taken.
            # if it's taken, we add the suffix "copy" to make it unique.
            name = self.main.check_name(name, self.main._templateModel.itemList())

            item = {
                '_name' : name,
                '_columns' : self.ui.columns.text(),
                '_rows' : self.ui.rows.text(),
                '_notes' : self.ui.notes.toPlainText()
            }

            command = ud.AddToTemplates(item, self.main._templateModel, self.main)
            self.main._undoStack.push(command)