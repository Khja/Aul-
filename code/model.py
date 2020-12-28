from PySide2 import QtCore
import data

class Node(object):
    def __init__(self, name, data, root=False, database=None):
        self._name = name
        self._data = data
        self._parent = None
        self._children = []
        self._row = 0
        self._column = 0
        self._columncount = 1
        if root:
            self._root = self
            self._id = 0
        if database != None:
            self._database = database

    def __repr__(self):
        return f'{self._name}'

    def data(self, column):
        if column >= 0 and column < len([self._name]):
            return self._name

    def columnCount(self):
        return self._columncount

    def childCount(self):
        return len(self._children)

    def child(self, row):
        if row >= 0 and row < self.childCount():
            return self._children[row]

    def addChild(self, child, obj_type, importing=False):
        # Create new child
        child._parent = self
        child._row = len(self._children)
        child._root = self._root
        child._database = self._database
        child._type = obj_type
        self._children.append(child)
        # Add child to database
        if importing == False:
            self._database.add(self._id, obj_type, child._name, child._data, self._root._name)
            child._id = self._database.last_id
        else:
            self._database.last_id += 1
        # Update ._columncount
        self._columncount = max(child.columnCount(), self._columncount)

    def removeChild(self, child, give=False):
        if child in self._children:
            self._children.remove(child)
            child._parent = None
            if give == True:
                return child
            return True
        return False

class Model(QtCore.QAbstractItemModel):
    def __init__(self, database, model_name): # Database object, model name in Database
        super(Model, self).__init__()
        self.headers = []
        self._root = Node(model_name, {}, True, database) # Create root
        self.nodes = {0:self._root} # id -> node
        self._model = model_name
        self.load()

    def __repr__(self):
        return self._model

    def load(self):
        branches = self._root._database.get(self._model)
        for n in branches:
            _id, parent_id, obj_type, name = n[0], n[1], n[2], n[3]
            data = self._root._database.dataToDict(n[4])
            node = Node(name, data)
            print(n)
            self.nodes[parent_id].addChild(node, obj_type, True)
            node._id = _id
            self.nodes[node._id] = node

    def rowCount(self,index):
        if index.isValid():
            return index.internalPointer().childCount()
        return self._root.childCount()

    def columnCount(self, index):
        if index.isValid():
            return index.internalPointer().columnCount()
        return self._root.columnCount()

    def addChild(self, node, obj_type, _parent=None):
        if not _parent or not _parent.isValid():
            parent = self._root
        else:
            parent = _parent.internalPointer()
        parent.addChild(node, obj_type)
        self.nodes[node._id] = node

    def removeChild(self, index):
        node = index.internalPointer() # get node that must be deleted
        parent_index = self.parent(index)  # get parent index
        parent = parent_index.internalPointer() # get parent node
        self.beginRemoveRows(parent_index, node._row, node._row)
        parent.removeChild(node)
        self.endRemoveRows()
        self.nodes[node._id] = None # remove from id -> node dict
        # remove from database
        self._root._database.remove([node._id])
        return True

    def child(self, index):
        if not index.isValid():
            return None
        node = index.internalPointer()
        return node

    def parent(self, index):
        if index.isValid():
            p = index.internalPointer()._parent
        if p:
            return QtCore.QAbstractItemModel.createIndex(self, p._row, 0, p)
        return QtCore.QModelIndex()

    def headerData(self, section, orientation, role=0):
        role =  QtCore.Qt.ItemDataRole(role)
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            if len(self.headers) > 0:
                return self.headers[section]
        return None

    def index(self, row, column, parent = None):
        if not parent or not parent.isValid():
            _parent = self._root
        else:
            _parent = parent.internalPointer()

        # if not QtCore.QAbstractItemModel.hasIndex(self, row, column, parent):
        #     return QtCore.QModelIndex()

        child = _parent.child(row)
        if child:
            return QtCore.QAbstractItemModel.createIndex(self, row, column, child)
        else:
            return QtCore.QModelIndex()

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            return node._name
        return None

    def editChild(self, index, name, new_data):
        node = index.internalPointer()
        node._name = name
        for d in new_data:
            node._data[d] = new_data[d]
        self._root._database.edit(node._id, node._name, node._data, node._parent._id)
        self.layoutChanged.emit()

    def moveChild(self, child, parent):
        # some bugs: deletes a child after a while of playing with moving around, then emits error
        childNode = child.internalPointer()
        oldParentNode = childNode._parent
        newParentNode = parent.internalPointer()
        ok = self.isParent(childNode, newParentNode)
        if ok:
            node = oldParentNode.removeChild(childNode, True)
            newParentNode.addChild(node, node._type)
            self.layoutChanged.emit()

    def isParent(self, child, parent): # child and parent are Node objects
        """check if the new parent of a child is not a child of the child"""
        grandparent = parent._parent
        if grandparent == None: # if it has no parent, it must be the root, which is fine
            return True
        elif grandparent == child: # in this case it's the child, so it can't be
            return False
        else:
            return self.isParent(child, grandparent) # recurse