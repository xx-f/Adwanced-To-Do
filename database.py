import sqlite3

def create_table():
    connection = sqlite3.connect('database.db')
    try:
        query = """Create table if not exists advToDo
        (
            id INTEGER PRIMARY KEY,
            name Not Null,
            description,
            date Not Null
        )
        """
        cur = connection.cursor()
        cur.execute(query)
        connection.commit()
    finally:
        connection.close()

def insert_deadline(name, desc, date):
    connection = sqlite3.connect('database.db')
    try:
        query = "insert into advToDo(name, description, date) values(?,?,?)"
        cur = connection.cursor()
        cur.execute(query, (name, desc, date))
        connection.commit()
    finally:
        connection.close()