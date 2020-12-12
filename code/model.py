import PySide2
import sys
from PySide2 import QtWidgets, QtCore

class Node(object):
    last_id = [0] # Not sure if this is still necessary
    def __init__(self, _data, _model, _parent, _id):#_model, _id, _parent, _name, _type='folder', _notes=''):
        for data in _data:
            setattr(self, data, _data[data])

        self._model = _model
        self._parent = _parent
        self._id = _id

        self._columncount = 1
        self._row = 0
        self._children = []

        self._id = _id
        self.id_()

    ################################
    def id_(self):
        # Set parent id
        if self._parent != None:
            self._parent_id = self._parent._id

        # Set an id
        if self._id == 1:
            # Create new id from last_id (variable common to all CustomItems)
            self.last_id[0] = self.last_id[0]+1
            self._id = self.last_id[0]

        # If it's the root, it has id 0
        elif self._id == 0:
            self._id = 0

    ################################
    def data(self, column):
        if column >= 0 and column < len([self._name]):
            return self._name

    def columnCount(self):
        return self._columncount

    def row(self):
        return self._row

    def childCount(self):
        return len(self._children)

    def child(self, row):
        if row >= 0 and row < self.childCount():
            return self._children[row]

    def parent(self):
        return self._parent

    def addChild(self, child):
        self._model.layoutAboutToBeChanged.emit()

        # Create new child
        child._parent = self
        child._parent_id = self._id
        child._row = len(self._children)
        child._model = self._model

        self._children.append(child)

        # Update ._columncount
        self._columncount = max(child.columnCount(), self._columncount)

        self._model.layoutChanged.emit()


class Tree(QtCore.QAbstractItemModel):
    def __init__(self, nodes = None):
        super(Tree, self).__init__()

        self.headers = []

        self._root = Node({}, self, None, 0) # Create root
        if nodes != None:
            for node in nodes:
                self._root.addChild(node)

    ################################
    def rowCount(self,index):
        if index.isValid():
            return index.internalPointer().childCount()
        return self._root.childCount()

    def columnCount(self, index):
        if index.isValid():
            return index.internalPointer().columnCount()
        return self._root.columnCount()

    ################################
    def addChild(self, node, _parent=None):
        if not _parent or not _parent.isValid():
            parent = self._root
        else:
            parent = _parent.internalPointer()
        parent.addChild(node)

    def child(self, index):
        if not index.isValid():
            return None
        node = index.internalPointer()
        return node

    def parent(self, index):
        if index.isValid():
            p = index.internalPointer().parent()
        if p:
            return QtCore.QAbstractItemModel.createIndex(self, p.row(), 0, p)
        return QtCore.QModelIndex()

    def headerData(self, section, orientation, role=0):
        role =  QtCore.Qt.ItemDataRole(role)
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            if len(self.headers) > 0:
                return self.headers[section]
        return None

    ################################
    def index(self, row, column, _parent = None):
        if not _parent or not _parent.isValid():
            parent = self._root
        else:
            parent = _parent.internalPointer()

        if not QtCore.QAbstractItemModel.hasIndex(self, row, column, _parent):
            return QtCore.QModelIndex()

        child = parent.child(row)
        if child:
            return QtCore.QAbstractItemModel.createIndex(self, row, column, child)
        else:
            return QtCore.QModelIndex()

    ################################
    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            return node.data(index.column())
        return None



class NodeDict(Node):
    def __init__(self, _data, _id, _model, _parent):
        self._data = _data

        self._model = _model
        self._parent = _parent
        self._columncount = 5
        self._row = 0
        self._children = []

        self._id = _id

    def data(self, column):
        if column >= 0 and column < len(self._data):
            return self._data[column]

class Dictionary(Tree):
    def __init__(self):
        super(Dictionary, self).__init__()

        self.headers = ['Word', 'Meaning', 'Class', 'Gender', 'Notes']

        self._root = NodeDict([], -1, self, None)



class Table(QtCore.QAbstractTableModel):
    def __init__(self, code, headers = [], parent=None):
        super(Table, self).__init__()
        self._data = [] # Must be a list with as many list as rows
        self.ver_headers = headers[0]
        self.hor_headers = headers[1]
        self._code = code

        self.hi = 0

    ################################
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if self._data:
            if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
                return self.hor_headers[section]
            if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Vertical:
                return self.ver_headers[section]

    def data(self, index, role):
        if self._data:
            if not index.isValid():
                return QtCore.QVariant()
            elif role != QtCore.Qt.DisplayRole:
                return QtCore.QVariant(QtCore.Qt.AlignTop)
            elif role == QtCore.Qt.SizeHintRole:
                return QtCore.QSize(item_width, 10)
            return QtCore.QVariant(self._data[index.row()][index.column()])
        return QtCore.QVariant([[0]][index.row()][index.column()])

    def hello(self):
        '''Is called only to update the table'''
        self.hi += 1
        return self.hi

    ################################
    def rowCount(self, parent):
        if self._data:
            return len(self._data)
        return 1

    def columnCount(self, parent):
        if self._data:
            return len(self._data[0])
        return 1



class Array(QtCore.QAbstractListModel):
    def __init__(self, main, items = []):
        super(Array, self).__init__()
        self.items = items
        self.main = main

        self.lastid = 0

    ################################
    def itemAt(self, index):
        if isinstance(index, int):
            return self.items[index]
        else:
            return self.items[index.row()]

    def getIndex(self, item):
        return self.items.index(item)

    def itemList(self):
        l = []
        for item in self.items:
            l.append(item['_name'])
        return l

    ################################
    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            item = self.items[index.row()]
            return item['_name']

    def rowCount(self, index):
        return len(self.items)

    ################################
    def add(self, item, index):
        if index != None:
            item['_id'] = index
            self.items.insert(index, item)
        else:
            item['_id'] = self.lastid
            self.lastid += 1
            self.items.append(item)

    def delete(self, item):
        self.items.remove(item)

