import model as md
import data as dt
from PySide2 import QtWidgets

class Add(QtWidgets.QUndoCommand):
    def __init__(self, node, obj_type, parent, model):
        super(Add, self).__init__()
        self._node = node
        self._type = obj_type
        self._parent = parent
        self._model = model
        self._redoMessage = f'Added "{self._node}" to [Parent] in {self._model._root._name[1:].capitalize()}'
        self._undoMessage = f'Undone adding "{self._node}" to [Parent] in {self._model._root._name[1:].capitalize()}'

    def redo(self):
        self._model.layoutAboutToBeChanged.emit()
        self._model.addChild(self._node, self._type, self._parent)
        self._index = self._model.index(self._node._row, self._node._column, self._parent)
        self._model.layoutChanged.emit()

    def undo(self):
        self._model.layoutAboutToBeChanged.emit()
        self._model.removeChild(self._index)
        self._model.layoutChanged.emit()

class Remove(QtWidgets.QUndoCommand):
    def __init__(self, index, model):
        super(Remove, self).__init__()
        self._index = index
        self._model = model

    def redo(self):
        self._model.layoutAboutToBeChanged.emit()
        # save data
        self._node = self._index.internalPointer()
        self._parent = self._model.parent(self._index)
        # remove child
        self._model.removeChild(self._index)
        self._model.layoutChanged.emit()
        self._redoMessage = f'Removed "{self._node}" from "{self._parent.internalPointer()}" in {self._model._root._name[1:].capitalize()}'

    def undo(self):
        self._model.layoutAboutToBeChanged.emit()
        self._model.addChild(self._node, self._node._type, self._parent)
        self._model.layoutChanged.emit()
        self._undoMessage = f'Undone removing "{self._node}" from "{self._parent.internalPointer()}" in {self._model._root._name[1:].capitalize()}'

class Edit(QtWidgets.QUndoCommand):
    def __init__(self, index, name, data, model):
        super(Edit, self).__init__()
        self._index = index
        self._old_name = name[0]
        self._new_name = name[1]
        self._old_data = data[0]
        self._new_data = data[1]
        self._model = model

    def redo(self):
        self._model.layoutAboutToBeChanged.emit()
        self._model.editChild(self._index, self._new_name, self._new_data)
        self._model.layoutChanged.emit()
        self._redoMessage = f'Changed data'

    def undo(self):
        self._model.layoutAboutToBeChanged.emit()
        self._model.editChild(self._index, self._old_name, self._old_data)
        self._model.layoutChanged.emit()
        self._undoMessage = f'Reverted data'

class Master():
    def __init__(self, filename, gui):
        self._database = dt.Database(filename)
        self._gui = gui
        self.trees = ('_morp', '_dict', '_temp', '_symb', '_rule', '_tabl')
        # create model for each model in Database
        for model in self.trees:
            setattr(self, model, md.Model(self._database, model))
        self._stack = QtWidgets.QUndoStack()

    def addChild(self, node, obj_type, model_name, parent=None):
        model = getattr(self, model_name)
        command = Add(node, obj_type, parent, model)
        self._stack.push(command)
        self._gui.ui.actionLbl.setText(command._redoMessage)

    def removeChild(self, index, model_name):
        model = getattr(self, model_name)
        command = Remove(index, model)
        self._stack.push(command)
        self._gui.ui.actionLbl.setText(command._redoMessage)

    def editData(self, index, model_name, new_data, new_name):
        model = getattr(self, model_name)
        node = index.internalPointer()
        old_data = {}
        for d in new_data:
            if d in node._data:
                old_data[d] = node._data[d]
            else:
                old_data[d] = None
        command = Edit(index, [node._name, new_name], [old_data, new_data], model)
        self._stack.push(command)