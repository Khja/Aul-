import sys
import PySide2
from PySide2 import QtWidgets, QtCore, QtGui

import main as mn
import model as md
import undo as ud
import const
import changer

class Edit(const.EditDialog):
    def __init__(self, main, node):
        super().__init__(main, node)
        self.ui = mn.loadUi('UI/table/edit_2.ui', self)
        self.setup()
        self.setup_templates()

        self.tree = self.main.table_rule_models[self.node._name]

        # change table when the template's changed
        self.ui.templates.currentIndexChanged.connect(self.load_template)

        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.table.cellClicked.connect(self.rule)

        # Rules window
        self.ui.rulesGrid.hide()
        self.ui.addBtn.clicked.connect(self.chooseToAdd)
        #self.ui.folderBtn.clicked.connect(self.addFolder)

        self.rules = self.main.all_rules[self.node._name]

        self.ui.generateBtn.clicked.connect(self.generate)

        self.ui.show()

    ################################
    def setup_templates(self):
        defined_templates = self.main._templateModel.itemList()

        # Templates comboBox
        templates = ['-- Choose template --']
        templates.extend(defined_templates)
        self.ui.templates.insertItems(0, templates)

        # Set index to right template, if there is any already chosen
        # It must be the template's name
        if self.node._template != None:
            index = 1 + defined_templates.index(self.node._template)
            self.ui.templates.setCurrentIndex(index)
            self.load_template()
        else:
            self.ui.templates.setCurrentIndex(0)

    def load_template(self):
        index = self.ui.templates.currentIndex() -1 # minus one because there is the "choose template" option

        if index >= 0:
            self.selected_template = self.main._templateModel.itemAt(index)

            # Table columns
            columns = self.selected_template['_columns']
            columns = columns.split(', ') # it is a string spaced by ", ", but we want a list
            self.ui.table.setColumnCount(len(columns))
            self.ui.table.setHorizontalHeaderLabels(columns)
            self.columns = len(columns)

            # Table rows
            rows = self.selected_template['_rows']
            rows = rows.split(', ') # same as above
            self.ui.table.setRowCount(len(rows))
            self.ui.table.setVerticalHeaderLabels(rows)
            self.rows = len(rows)

        else:
            # empty when not chosen template
            self.ui.table.setColumnCount(0)
            self.ui.table.setHorizontalHeaderLabels([])

            self.ui.table.setRowCount(0)
            self.ui.table.setVerticalHeaderLabels([])

        # Stretch headers to fit size
        self.ui.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.ui.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)


    ################################
    def save(self):
        old_data, new_data = self.data()
        old_data['_template'] = self.node._template

        # retrieve node's template if there is one
        index = self.ui.templates.currentIndex() - 1

        template = None

        if self.main._templateModel.rowCount(0) > 0:
            if index > -1: # If it is -1 it is on "choose template"
                template = self.main._templateModel.itemAt(index)
                template = template['_name']

        new_data['_template'] = template

        self.push(old_data, new_data, self.node)

    def rule(self, row, column):
        self.ui.rulesGrid.show()
        cell = (row, column)
        if cell in self.tree:
            self.ui.treeView.setModel(self.tree[cell]) # it has only sense to show the tree if there is one
        else:
            self.ui.treeView.setModel(md.Tree())
        self.currentCell = cell

    def chooseToAdd(self):
        self.choice = ChooseRule(self, self.main)

    def setModel(self):
        if self.currentCell not in self.tree:
            self.tree[self.currentCell] = md.Tree() # add a treemodel if there isn't one yet; do it now, so to not have to hold many tree in memory
            self.ui.treeView.setModel(self.tree[self.currentCell]) # connect tree to display it

    def add(self, data):
        if data != None:
            self.setModel()
            node = md.Node(data, self.tree[self.currentCell], None, 1)
            self.tree[self.currentCell].addChild(node)
            self.main.table_rule_models[self.node._name] = self.tree

    def generate(self):
        word = self.ui.example.text()
        cells = self.getRules() # convert the model with the models to a dict with lists of the rules
        for c in cells:
            rules = cells[c]
            w = '' + word
            for r in rules:
                w = changer.change(r['_form'], r['_before'], r['_what'], r['_after'], r['_change'], w)
            item = QtWidgets.QTableWidgetItem(w)
            self.ui.table.setItem(c[0], c[1], item)

    def getRules(self):
        rules = {}
        for x in range(self.columns):
            for y in range(self.rows):
                rules[(y, x)] = []
                if (y, x) in self.tree:
                    model = self.tree[(y, x)]
                    root = model._root
                    r = self.getChildrenRules(root)
                    rules[(y, x)].extend(r)
        return rules

    def getChildrenRules(self, r):
        children = r._children
        m = [c._data for c in children]
        for c in children:
            k = self.getChildrenRules(c)
            if type(k) == list:
                m.extend([c._data for c in k])
            else:
                m.append(k._data)
        return m

class ChooseRule(QtWidgets.QDialog):
    def __init__(self, parent, main):
        super(ChooseRule, self).__init__()
        self.ui = mn.loadUi('UI/table/choose_rule.ui', self)

        self.parent = parent
        self.main = main

        self.ui.addBtn.clicked.connect(self.new)
        self.ui.deleteBtn.clicked.connect(self.delete)

        self.model = self.parent.rules
        #self.rule_n = len(self.model.items)
        self.ui.treeView.setModel(self.model)
        self.ui.buttonBox.accepted.connect(self.chosen)

        # combobox where you see all table names to choose from, to get rules of them
        ## missing: set index to current table name
        ## possible improvement: search for table name
        items = [name for name in self.parent.main.all_rules]
        items.insert(0, '-- Choose table --')
        self.ui.comboBox.insertItems(0, items)

        self.ui.show()

    def addToModel(self, node):
        if node != False:
            self.model.addChild(node)
            self.model.layoutChanged.emit()
            self.parent.main.cursor.execute(
                'INSERT INTO tablerules (_id, _name, _parent, _table, _type, _data) VALUES (?, ?, ?, ?, ?, ?)',
                (
                    node._id,
                    node._name,
                    node._parent._id,
                    self.parent.node._name,
                    'rule',
                    f"{node._data['_form']}, {node._data['_before']}, {node._data['_what']}, {node._data['_after']}, {node._data['_change']}",
                )
            )
            print(node)

    def new(self):
        self.n = NewRule(self, self.main)

    def chosen(self):
        selected = self.ui.treeView.selectionModel().selectedRows()
        if len(selected) > 0: # If there is a selection in the tree
            selection = selected[0] # The index of the selected node in tree
            node = selection.internalPointer() # get node object
            data = {'_data': node._data, '_name': node._name} # transfer data to new dict
            self.parent.add(data)

    def delete(self):
        # Bug when deleting and then saying 'ok'
        selected = self.ui.treeView.selectionModel().selectedRows()
        if len(selected) > 0:
            selection = selected[0]
            node = selection.internalPointer()
            node._parent._children.remove(node)
            self.model.layoutChanged.emit()

class NewRule(QtWidgets.QDialog):
    def __init__(self, parent, main):
        super(NewRule, self).__init__()
        self.ui = mn.loadUi('UI/table/add_rule.ui', self)
        self.parent = parent
        self.main = main

        self.ui.buttonBox.accepted.connect(self.add)

        self.ui.show()

    def add(self):
        form, before, what, after, change = self.ui.form.text(), self.ui.before.text(), self.ui.what.text(), self.ui.after.text(), self.ui.change.text()
        name = self.ui.name.text()

        if len(name) == 0:
            name = 'Rule'

        if len(form + before + what + after + change) > 0:
            data = {
                '_name': name,
                '_form': form,
                '_before': before,
                '_what': what,
                '_after': after,
                '_change': change
            }
            d = {'_data':data, '_name': data['_name']}
            node = md.Node(
                d,
                self.parent.parent.rules,
                None,
                1
            )
            self.parent.addToModel(node)
