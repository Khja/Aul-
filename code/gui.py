from PySide2 import QtWidgets, QtCore, QtGui, QtUiTools
import model as md
import data as dt
import master as ms

def loadUi(filename, parent=None):
    loader = QtUiTools.QUiLoader()
    ui = loader.load(filename, parent)
    return ui

class EditDialog(QtWidgets.QDialog):
    def setup(self, filename, main_window, node=None):
        super(EditDialog, self).__init__()
        self.ui = loadUi(filename, self)
        self.main = main_window
        self.ui.buttonBox.accepted.connect(self.done)
        self.ui.show()
        if node != None:
            self.ui.nameLine.setText(node._name)

    def done(self):
        pass

    def getData(self, attribute, node):
        if attribute in node._data:
            return node._data[attribute]
        return ''

class AddDialog(EditDialog):
    def __init__(self, proper_type, main_window):
        self.setup('ui/add.ui', main_window)
        self.ui.typeCombo.insertItem(0, proper_type)

    def done(self):
        name, obj_type = self.ui.nameLine.text(), self.ui.typeCombo.currentText()
        self.main.addAction(name, obj_type)

class Folder(EditDialog):
    def __init__(self, main_window, node):
        self.setup('ui/add.ui', main_window, node)
        self.ui.typeCombo.hide()
        self.ui.typeLbl.hide()
        self.ui.setWindowTitle('Edit')

    def done(self):
        name = self.ui.nameLine.text()
        self.main.editAction({}, name)

class Note(EditDialog):
    def __init__(self, main_window, node):
        self.setup('ui/note.ui', main_window, node)
        if '_text' in node._data:
            self.ui.textEdit.setHtml(node._data['_text'])

    def done(self):
        text = self.ui.textEdit.toHtml()
        name = self.ui.nameLine.text()
        self.main.editAction({'_text': text}, name)

class SelectTemplate(EditDialog):
    def __init__(self, main_window, table_window):
        self.setup('ui/selecttemplate.ui', main_window)
        self.tableDialog = table_window
        self.model = self.main._master._temp
        self.ui.treeView.setModel(self.model)

    def done(self):
        selection = self.ui.treeView.selectionModel().selectedRows()
        if len(selection) > 0:
            index = selection[0]
        else:
            index = None
        self.tableDialog.selected(index)

class Symbol(EditDialog):
    def __init__(self, main_window, node):
        self.setup('ui/symbol.ui', main_window, node)
        self.ui.symbolLine.setText(self.getData('_symbol', node))
        self.ui.regexLine.setText(self.getData('_regex', node))

    def done(self):
        name = self.ui.nameLine.text()
        symbol = self.ui.symbolLine.text()
        regex = self.ui.regexLine.text()
        self.main.editAction({'_symbol':symbol, '_regex':regex}, name)

def tableSetup(ui):
    ui.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    ui.tableWidget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

def setHeaders(dimensions, ui):
    rows, columns = dimensions
    rowDelta = len(rows) - ui.tableWidget.rowCount()
    columnDelta = len(columns) - ui.tableWidget.columnCount()
    if rowDelta > 0: # if there are more rows in rowLine
        for i in range(rowDelta):
            ui.tableWidget.insertRow(0)
    elif rowDelta < 0: # if there are less rows in rowLine
        for i in range(0 - rowDelta):
            ui.tableWidget.removeRow(0)
    if columnDelta > 0: # if there are more columns in columnLine
        for i in range(columnDelta):
            ui.tableWidget.insertColumn(0)
    elif columnDelta < 0: # if there are less columns in columnLine
        for i in range(0 - columnDelta):
            ui.tableWidget.removeColumn(0)
    ui.tableWidget.clear() # reset header names
    ui.tableWidget.setHorizontalHeaderLabels(columns)
    ui.tableWidget.setVerticalHeaderLabels(rows)

class Template(EditDialog):
    def __init__(self, main_window, node):
        self.setup('ui/template.ui', main_window, node)
        tableSetup(self.ui)
        self.ui.rowLine.setText(self.getData('_rows', node))
        self.ui.columnLine.setText(self.getData('_columns', node))
        setHeaders(self.dimensions(), self.ui)
        self.ui.columnLine.editingFinished.connect(lambda:setHeaders(self.dimensions(), self.ui))
        self.ui.rowLine.editingFinished.connect(lambda:setHeaders(self.dimensions(), self.ui))

    def dimensions(self):
        rows = self.ui.rowLine.text().split(', ')
        columns = self.ui.columnLine.text().split(', ')
        return (rows, columns)

    def done(self):
        name = self.ui.nameLine.text()
        rows = self.ui.rowLine.text()
        columns = self.ui.columnLine.text()
        self.main.editAction({'_rows':rows, '_columns':columns}, name)

class Window(QtWidgets.QMainWindow):
    def setup(self, filename):
        super(Window, self).__init__()
        self.ui = loadUi(filename, self)
        self.ui.menubar.triggered.connect(self.actionClicked)
        self.ui.show()

    def actionClicked(self, action): # connects each shortcut/menubar item to its respective function
        name = action.text()
        command = getattr(self, name.lower())
        command()

class Table(Window):
    def __init__(self, main_window, node):
        self.setup('ui/table2.ui')
        self.main = main_window
        self.dimensions = self.getDimensions(node)
        self.template = self.getData('_template', node)
        tableSetup(self.ui)
        self.setTable()
        self.setRules(node)
        self.ui.buttonBox.accepted.connect(self.done)
        self.ui.buttonBox.rejected.connect(self.ui.destroy) # you can use the hide method, but don't know the difference
        self.ui.selectBtn.clicked.connect(self.selectTemplate)
        self.ui.nameLine.setText(node._name)

    def getData(self, attribute, node):
        if attribute in node._data:
            return node._data[attribute]
        return ''

    def done(self):
        name = self.ui.nameLine.text()
        rows = ', '.join(self.dimensions[0])
        columns = ', '.join(self.dimensions[1])
        self.main.editAction({'_rows':rows, '_columns':columns, '_template':self.template}, name)
        self.ui.destroy()

    def selectTemplate(self):
        self.selectWindow = SelectTemplate(self.main, self)

    def selected(self, index):
        if index != None:
            node = index.internalPointer()
            self.dimensions = self.getDimensions(node)
            self.template = node._name
            self.setTable()

    def getDimensions(self, node):
        data = []
        for d in ('_rows', '_columns'):
            if d in node._data:
                l = node._data[d].split(', ')
                data.append(l)
            else:
                data.append([])
        return tuple(data)

    def setTable(self):
        setHeaders(self.dimensions, self.ui)
        self.ui.currentLbl.setText(self.template)

    def setRules(self, node):
        model_name = f'table_{node._name}'
        if model_name in self.main._master.table_rules: # is there a model for the table node?
            self.ruleModel = getattr(self.main._master.table_rules, node._name) # retrieve it
        else:
            self.main._master.table_rules.append(model_name)
            self.ruleModel = md.Model(self.main._master._database, model_name)
            setattr(self.main._master, model_name, self.ruleModel)
            if '_rows' in node._data and '_columns' in node._data:
                rows = node._data['_rows'].split(', ')
                for column in node._data['_columns'].split(', '):
                    column_node = md.Node(column, {})
                    self.ruleModel.addChild(column_node, 'Cell')
                    for row in rows:
                        row_node = md.Node(row, {})
                        parent = self.ruleModel.index(column_node._row, column_node._column)
                        self.ruleModel.addChild(row_node, 'Cell', parent)
        self.ui.treeView.setModel(self.ruleModel) # set the model for the rules

    def add(self):
        self.addDialog = AllRules(self.main, self)

class AllRules(EditDialog):
    def __init__(self, main_window, table_window):
        self.setup('ui/allrules.ui', main_window)
        self.tableDialog = table_window
        self.model = self.main._master._rule
        self.ui.treeView.setModel(self.model)
class SelectTemplate(EditDialog):
    def __init__(self, main_window, table_window):
        self.setup('ui/selecttemplate.ui', main_window)
        self.tableDialog = table_window
        self.model = self.main._master._temp
        self.ui.treeView.setModel(self.model)

    def done(self):
        selection = self.ui.treeView.selectionModel().selectedRows()
        if len(selection) > 0:
            index = selection[0]
        else:
            index = None
        self.tableDialog.selected(index)




class Symbol(EditDialog):
    def __init__(self, main_window, node):
        self.setup('ui/symbol.ui', main_window, node)
        self.ui.symbolLine.setText(self.getData('_symbol', node))
        self.ui.regexLine.setText(self.getData('_regex', node))

    def done(self):
        name = self.ui.nameLine.text()
        symbol = self.ui.symbolLine.text()
        regex = self.ui.regexLine.text()
        self.main.editAction({'_symbol':symbol, '_regex':regex}, name)

class MainWindow(Window):
    def __init__(self, app):
        self.setup('ui/test.ui')
        self._app = app
        self._master = ms.Master('data.test', self)
        self.moving = []
        for t in ('morp', 'dict', 'temp', 'symb'):
            tree = getattr(self._master, f'_{t}')
            model = getattr(self.ui, f'{t}TreeView')
            model.setModel(tree)
        self.ui.morpTreeView.doubleClicked.connect(self.move)

    def currentTree(self):
        tab = self.ui.tabWidget.currentIndex()
        return self._master.trees[tab]

    def getSelection(self):
        tree_name = self.currentTree()
        tree = getattr(self.ui, f'{tree_name[1:]}TreeView')
        selection = tree.selectionModel().selectedRows()
        if len(selection) > 0:
            return selection[0]
        return None

    def delete(self):
        selected = self.getSelection()
        self._master.removeChild(selected, self.currentTree())

    def add(self):
        tree = self.currentTree()
        objects = {'_morp':'Table', '_dict':'Word', '_temp':'Template', '_symb':'Symbol', '_rule':'Rule', '_tabl':'Rule'}
        comboItem = objects[tree]
        self.addDialog = AddDialog(comboItem, self)

    def addAction(self, name, obj_type):
        selected = self.getSelection()
        self._master.addChild(md.Node(name, {}), obj_type, self.currentTree(), selected)

    def edit(self):
        selected = self.getSelection()
        if selected != None:
            node = selected.internalPointer()
            nodes = {'Folder':Folder, 'Note':Note, 'Table':Table, 'Template':Template, 'Symbol':Symbol}
            if node._type in nodes:
                self.editDialog = nodes[node._type](self, node)

    def editAction(self, new_data, new_name):
        selected = self.getSelection()
        self._master.editData(selected, self.currentTree(), new_data, new_name)

    def move(self):
        selected = self.getSelection()
        self.moving.append(selected)
        if len(self.moving) > 1:
            print(self.moving)
            self._master._morp.moveChild(self.moving[0], self.moving[1])
            self.moving = []

    def undo(self):
        if self._master._stack.canUndo() is True:
            self._master._stack.undo()
            command = self._master._stack.command(self._master._stack.index())
            self.ui.actionLbl.setText(command._undoMessage)

    def redo(self):
        if self._master._stack.canRedo() is True:
            command = self._master._stack.command(self._master._stack.index())
            self.ui.actionLbl.setText(command._redoMessage)
            self._master._stack.redo()

    def save(self):
        self._master._database.close()

    def deselect(self):
        tree = self.currentTree()
        view = getattr(self.ui, f'{tree[1:]}TreeView')
        selectionModel = view.selectionModel()
        selectionModel.clear()

if __name__ == '__main__':
    import sys
    Aule = QtWidgets.QApplication(sys.argv)
    Aule.setQuitOnLastWindowClosed(False)
    window = MainWindow(Aule)
    sys.exit(Aule.exec_())