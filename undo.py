import PySide2
from PySide2 import QtWidgets, QtCore

import model

class AddToTree(QtWidgets.QUndoCommand):
    def __init__(self, node, parent, main):
        super(AddToTree, self).__init__()
        self.node = node
        self._model = self.node._model
        self.parent = parent
        self.main = main

        if self.node._type == 'Table':
            self.node._template = None
        elif self.node._type == 'Class':
            self.node._genders = None

    def redo(self):
        self.node._model.layoutAboutToBeChanged.emit()
        self.node._model.addChild(self.node, self.parent)
        self.node._model.layoutChanged.emit()

        # We put this here so that the program doesn't crash when
        # we call the undo function:
        self._parent = self.node._parent

        # create a new row in database-file
        self.main.cursor.execute(
            """INSERT INTO tree
            (_id, _parent, _name, _type, _notes)
            VALUES (?, ?, ?, ?, ? )""",
            (
                self.node._id,
                self.node._parent_id,
                self.node._name,
                self.node._type,
                self.node._notes
            )
        )
        self.main.conn.commit()

    def undo(self):
        self.node._model.layoutAboutToBeChanged.emit()
        self._parent._children.remove(self.node)
        self.node._model.layoutChanged.emit()

        # delete row in database-file
        self.main.cursor.execute(
            "DELETE FROM tree WHERE _id = ?",
            (self.node._id,)
        )
        self.main.conn.commit()


class DeleteNode(QtWidgets.QUndoCommand):
    def __init__(self, node, main):
        super(DeleteNode, self).__init__()

        self.node = node
        self._model = self.node._model
        self._parent = self.node._parent
        self.main = main

    def redo(self):
        self.node._model.layoutAboutToBeChanged.emit()
        self._parent._children.remove(self.node)
        self.node._model.layoutChanged.emit()

        # delete row in database-file
        self.main.cursor.execute(
            "DELETE FROM tree WHERE _id = ?",
            (self.node._id,)
        )
        self.main.conn.commit()

    def undo(self):
        self._model.layoutAboutToBeChanged.emit()
        self._parent.addChild(self.node)
        self._model.layoutChanged.emit()

        self._parent = self.node._parent

        # create a new row in database-file
        self.main.cursor.execute(
            """INSERT INTO tree
            (_id, _parent, _name, _type, _notes)
            VALUES (?, ?, ?, ?, ? )""",
            (
                self.node._id,
                self.node._parent_id,
                self.node._name,
                self.node._type,
                self.node._notes
            )
        )
        self.main.conn.commit()


class EditNode(QtWidgets.QUndoCommand):
    def __init__(self, old, new, node, main):
        super(EditNode, self).__init__()
        self.old = old # dict
        self.new = new # dict
        self.node = node
        self.main = main

    def redo(self):
        self.node._model.layoutAboutToBeChanged.emit()
        for data in self.new:
            setattr(self.node, data, self.new[data])

        self.node._model.layoutChanged.emit()

        self.update_database(self.new)

    def undo(self):
        self.node._model.layoutAboutToBeChanged.emit()
        for data in self.old:
            setattr(self.node, data, self.old[data])
        self.node._model.layoutChanged.emit()

        self.update_database(self.old)

    def update_database(self, data):
        # since every node in the tree has different attributes,
        # we create a list of the attribute names we mus update

        updating = ''

        for i in data:
            updating += f'{i} = ?, '

        updating = updating[:-2] # delete last comma

        # next we create a list of all the info in the
        # variable "updating"'s order

        info = [data[attribute] for attribute in data]
        info.append(self.node._id)
        info = tuple(info) # tuple format is needed

        self.main.cursor.execute(
            f"UPDATE tree SET {updating} WHERE _id = ?",
            info
        )
        self.main.conn.commit()

class AddToList(QtWidgets.QUndoCommand):
    def __init__(self, item, model):
        super(AddToList, self).__init__()
        self.item = item
        self.model = model
        self.index = None

    def redo(self):
        self.model.add(self.item, self.index)
        self.model.layoutChanged.emit()
        self.index = self.model.getIndex(self.item)
        self.item = self.model.itemAt(self.index)

    def undo(self):
        self.model.delete(self.item)
        self.model.layoutChanged.emit()

class AddToTemplates(AddToList):
    def __init__(self, item, model, main):
        super().__init__(item, model)
        self.main = main

    def redo(self):
        super().redo()

        self.item = self.model.itemAt(self.index)
        self.main.cursor.execute(
            'INSERT INTO templates (_name, _rows, _columns, _notes, _id) VALUES (?, ?, ?, ?, ?)',
            (
                self.item['_name'],
                self.item['_rows'],
                self.item['_columns'],
                self.item['_notes'],
                self.index
            )
        )
        self.main.conn.commit()

    def undo(self):
        super().undo()
        self.main.cursor.execute(
            'DELETE FROM templates WHERE _id = ?',
            (self.index,)
        )
        self.main.conn.commit()


class AddWord(QtWidgets.QUndoCommand):
    def __init__(self, node, main):
        super(AddWord, self).__init__()
        self.node = node
        self.main = main

    def redo(self):
        self.node._model.layoutAboutToBeChanged.emit()
        self.node._model.addChild(self.node)
        self.node._model.layoutChanged.emit()

        data = self.node._data
        self.node._id = dictNewId(self.main.cursor)

        self.main.cursor.execute(
            'INSERT INTO dictionary (_id, _word, _meaning, _class, _gender, _notes) VALUES (?, ?, ?, ?, ?, ?)',
            (self.node._id, data[0], data[1], data[2], data[3], data[4], )
        )
        self.main.conn.commit()

    def undo(self):
        self.node._model.layoutAboutToBeChanged.emit()
        self.node._model._root._children.remove(self.node)
        self.node._model.layoutChanged.emit()

        self.main.cursor.execute('DELETE FROM dictionary WHERE _id = ?', (self.node._id,))
        self.main.conn.commit()

class DeleteWord(QtWidgets.QUndoCommand):
    # There's a bug that seems to reduplicate the deleted node when adding it back
    def __init__(self, node, main):
        super(DeleteWord, self).__init__()
        self.node = node
        self.main = main

    def redo(self):
        self.node._model.layoutAboutToBeChanged.emit()
        self.node._model._root._children.remove(self.node)
        self.node._model.layoutChanged.emit()

        self.main.cursor.execute('DELETE FROM dictionary WHERE _id = ?', (self.node._id,))
        self.main.conn.commit()

    def undo(self):
        self.node._model.layoutAboutToBeChanged.emit()
        self.node._model.addChild(self.node)
        self.node._model.layoutChanged.emit()

        data = self.node._data
        self.node._id = dictNewId(self.main.cursor)

        self.main.cursor.execute(
            'INSERT INTO dictionary (_id, _word, _meaning, _class, _gender, _notes) VALUES (?, ?, ?, ?, ?, ?)',
            (self.node._id, data[0], data[1], data[2], data[3], data[4], )
        )

        self.main.conn.commit()


def dictNewId(cursor):
    cursor.execute('SELECT * FROM dictionary ORDER BY _id DESC LIMIT 1')
    selection = cursor.fetchone()
    if selection == None:
        return 0
    else:
        return selection[0] + 1