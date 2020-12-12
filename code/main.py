import sys
import PySide2
from PySide2 import QtWidgets, QtCore, QtGui, QtUiTools
import sqlite3
from PySide2.QtUiTools import QUiLoader

import model as md
import undo as ud
import windows.templates as tp
import windows.tree as bo
import windows.table as tb
import windows.syntax as sy
import windows.classes as cl
import windows.dictionary as dc

"""
Aule - Simple conlanging software tool
Copyright (C) 2020 Khja
"""

def loadUi(filename, parent=None):
    loader = QtUiTools.QUiLoader()
    ui = loader.load(filename, parent)

    return ui

# Possible bugs:
# there may be errors for the method "check_name";
# I do not know if I've cleaned everything or if there is
# such method being used other than in the templates
# Opening and closing must be thouroughly checked,
# as I don't know if everything is okay

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.ui = loadUi('UI/main2.ui', self)
        self.app = app

        ## MODELS
        self._templateModel = md.Array(self)
        self._treeModel = md.Tree()
        self._dictModel = md.Dictionary()
        self.ui.treeView.setModel(self._treeModel)
        self.ui.treeView.doubleClicked.connect(self.editTree)
        self.ui.dictionaryView.setModel(self._dictModel)
        self.ui.dictionaryView.doubleClicked.connect(self.hello)

        # UNDO
        self._undoStack = QtWidgets.QUndoStack(self)

        # MENU BAR FUNCTIONS
        self.ui.menubar.triggered.connect(self.actionClicked)

        # Rules
        self.all_rules = {}
        self.table_rule_models = {}

        # Ask for filename
        filename = None
        dialog = QtWidgets.QFileDialog(self)
        dialog.setNameFilter(("Khuzdul files (*.khz);;All files (*.*)"))
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]

        # Open file or create new one
        if filename == None:
            self.new_file()
        else:
            self.load_file(filename)

        # Dictionary
        self.ui.dictGroup.hide()
        self.ui.show()
        self.ui.installEventFilter(self)

    ################################
    ## Files
    ################################
    def new_file(self):
        """creates a database file"""

        self.conn = sqlite3.connect('file.khz')
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE tree (_id integer, _parent integer, _name text, _type text, _notes text, _genders text, _template text)')
        self.cursor.execute('CREATE TABLE templates (_id integer, _name text, _rows text, _columns text, _notes text)')
        self.cursor.execute('CREATE TABLE dictionary (_id INT PRIMARY KEY, _word text, _meaning text, _class text, _gender text, _notes text)')

    def open_file(self, filename):
        self.conn = sqlite3.connect(filename)
        self.cursor = self.conn.cursor()
        self.filename = filename
        #self.cursor.execute('DROP TABLE dictionary')
        #self.cursor.execute('CREATE TABLE dictionary (_id INT PRIMARY KEY, _word text, _meaning text, _class text, _gender text, _notes text)')


    def load_file(self, filename):
        self.open_file(filename)
        self.treeLoad()
        self.dictLoad()

    def dictLoad(self):
        words = self.cursor.execute('SELECT * FROM dictionary ORDER BY _word')
        for word in words:
            data = [
                word[1],
                word[2],
                word[3],
                word[4],
                word[5]
            ]
            node = md.NodeDict(data, word[0], self._dictModel, None)
            self._dictModel.addChild(node)

    def treeLoad(self):
        # add templates
        templates = self.cursor.execute('SELECT * FROM templates ORDER BY _id')
        template_dims = {}

        for template in templates:
            item = {
                '_name' : template[1],
                '_rows' : template[2],
                '_columns' : template[3],
                '_notes' : template[4]
            }
            template_dims[template[1]] = (len(template[2].split(', ')), len(template[3].split(', '))) # Store template dimensions for later recall

            self._templateModel.add(item, template[0])

        # add nodes to tree
        nodes = self.cursor.execute('SELECT * FROM tree ORDER BY _id')
        added_nodes = {0: self._treeModel} # This is here for reference when creating the connection between nodes

        for node in nodes:
            data = {
                '_name': node[2],
                '_type': node[3],
                '_notes': node[4]
            }

            if data['_type'] == 'Table':
                data['_template'] = node[6]
                self.all_rules[data['_name']] = md.Tree() ## change this to import rules

                self.table_rule_models[data['_name']] = {}

            elif data['_type'] == 'Class':
                data['_genders'] = node[5]

            _id = node[0]
            _parent = node[1]

            new = md.Node(data, self._treeModel, None, _id)

            added_nodes[_parent].addChild(new) # The node at _parent position in the dict is the parent
            added_nodes[_id] = new # Add the node to the added_nodes dict for future reference
            new.last_id[0] = new.last_id[0] + 1

    # @QtCore.Slot()
    # Using this provokes a bug, I don't know how to solve
    # def eventFilter(self, target, event):
        # if event.type() == QtCore.QEvent.Type.Close:
            # self.conn.commit()
            # self.conn.close()
            # self.app.setQuitOnLastWindowClosed(True)

    def save(self):
        self.conn.commit()
        self.conn.close()
        self.conn = sqlite3.connect(self.filename)
        self.cursor = self.conn.cursor()

    ################################
    ## Undo
    ################################
    def undo(self):
        '''Call last undo object'''
        if self._undoStack.canUndo() is True:
            self._undoStack.undo()

    def redo(self):
        '''Call last redo object'''
        if self._undoStack.canRedo() is True:
            self._undoStack.redo()

    ################################
    ## Shortcut handlers
    ################################
    def actionClicked(self, action):
        """This connects each shortcut/menbar item
            to its respective function"""
        name = action.text()

        if name == "Undo":
            self.undo()

        elif name == "Redo":
            self.redo()

        elif name == "Add":
            self.dictOrTree(self.addTree, self.addDict)

        elif name == "Delete":
            self.dictOrTree(self.deleteTree, self.deleteDict)

        elif name == "Edit":
            self.dictOrTree(self.editTree, self.editDict)

        elif name == "Templates":
            self.templates()

        elif name == "Dictionary":
            self.ui.dictGroup.show()
            self.ui.treeGroup.hide()

        elif name == "Tree":
            self.ui.treeGroup.show()
            self.ui.dictGroup.hide()

        elif name == "Save":
            self.save()

    # Dummy method
    def hello(self):
        print('hi')

    def dictOrTree(self, t, d):
        if self.ui.treeGroup.isVisible():
            t()
        elif self.ui.dictGroup.isVisible():
            d()

    ################################
    def check_name(self, name, l):
        '''This recursive method makes sure that the selected name is unique'''
        if name in l:
            return self.check_name(name + ' copy', l)
        else:
            return name

    ################################
    ## Tree
    ################################
    def templates(self):
        '''Shows a dialog with all the defined table templates'''
        self.templateDialog = tp.ManageTemplates(self)

    def addTree(self):
        '''Shows a dialog where you can add objects to the tree'''
        selected_rows = self.ui.treeView.selectionModel().selectedRows()

        if len(selected_rows) > 0: # If there is a selection in the tree
            selection = selected_rows[0] # The index of the selected node in tree
            self.addTreeDialog = bo.Add(self, selection)
        else:
            self.addTreeDialog = bo.Add(self)

    def editTree(self):
        selected_rows = self.ui.treeView.selectionModel().selectedRows()

        if len(selected_rows) > 0:
            selection = selected_rows[0] # The index of the selected node in tree
            node = selection.internalPointer()

            if node._type == 'Folder':
                self.editDialog = bo.Edit(self, node)
            elif node._type == 'Class':
                self.editDialog = cl.Edit(self, node)
            elif node._type == 'Table':
                self.editDialog = tb.Edit(self, node)
            elif node._type == 'Syntax':
                self.editDialog = sy.Edit(self, node)

    def deleteTree(self):
        selected_rows = self.ui.treeView.selectionModel().selectedRows()
        if len(selected_rows) > 0:
            selection = selected_rows[0] # The index of the selected node in tree
            node = selection.internalPointer()
            command = ud.DeleteNode(node, self)
            self._undoStack.push(command)

    ################################
    ## Dictionary
    ################################
    def addDict(self):
        self.addDictDialog = dc.Add(self) ## see notes in dictionary.py

    def editDict(self):
        selected_rows = self.ui.dictionaryView.selectionModel().selectedRows()
        if len(selected_rows) > 0:
            selection = selected_rows[0]
            node = selection.internalPointer()

            self.editDictDialog = dc.Add(self, node)

    def deleteDict(self):
        selected_rows = self.ui.dictionaryView.selectionModel().selectedRows()
        if len(selected_rows) > 0:
            selection = selected_rows[0]
            node = selection.internalPointer()
            command = ud.DeleteWord(node, self)
            self._undoStack.push(command)
