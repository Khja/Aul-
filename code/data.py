import sqlite3

class Database():
    def __init__(self, filename):
        self.filename = filename
        self.connection = sqlite3.connect(filename)
        self.cursor = self.connection.cursor()
        self.last_id = 0
        self.genTables()

    def genTables(self):
        try:
            command = "CREATE TABLE data (_id integer, _parent integer, _type text, _name text, _data text, _model text)"
            self.cursor.execute(command)
            self.connection.commit()
        except:
            pass

    def dataToDatabase(self, d):
        _data = ""
        for i in d:
            _data += f'"{i}":"{d[i]}"/; '
        _data = _data[:-3] # remove last space and comma
        return _data

    def dataToDict(self, d):
        if len(d) > 0:
            datalist = d.split('/; ')
            _data = {}
            for i in datalist:
                item = i[1:-1] # remove quotes
                keyNstring = item.split('":"') # split into key and string
                _data[keyNstring[0]] = keyNstring[1]
            return _data
        return {}

    def get(self, m): # get all data of type t
        command = "SELECT * FROM data WHERE _model = ? ORDER BY _id"
        self.cursor.execute(command, (m,))
        data = self.cursor.fetchall()
        return data

    def close(self):
        self.connection.commit()
        self.connection.close()
        return True

    def next_id(self):
        self.last_id += 1
        return self.last_id

    def add(self, p, t, n, d, m): # parent, type, name, data
        command = "INSERT INTO data (_id, _parent, _type, _name, _data, _model) VALUES (?, ?, ?, ?, ?, ?)"
        _data = self.dataToDatabase(d)
        i = self.next_id()
        self.cursor.execute(command, (i, p, t, n, _data, m))

    def remove(self, parents): # remove node from [id]. A list is used so that it can recurse, if there the node has children
        children = []
        for i in parents:
            remove = "DELETE FROM data WHERE _id = ?"
            self.cursor.execute(remove, (i,))
            # select all children
            select = "SELECT * FROM data WHERE _parent = ?"
            self.cursor.execute(select, (i,))
            ids = [d[0] for d in self.cursor.fetchall()] # get the ids of the children
            children.extend(ids)
        if len(children) > 0: # if there are children repeat for each child
            self.remove(children)

    def edit(self, i, n, d, p): # id, new name, new data, new parent
        command = "UPDATE data SET _name = ?, _data = ?, _parent = ? WHERE _id = ?"
        _data = self.dataToDatabase(d)
        self.cursor.execute(command, (n, _data, p, i))