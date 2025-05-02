import sqlite3

def create_database():
    conn = sqlite3.connect('./database/plates.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS plates (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, name2 TEXT, national_code TEXT, plate TEXT)''')
    conn.commit()
    conn.close()

def insert_sample_data():
    conn = sqlite3.connect('./database/plates.db')
    c = conn.cursor()
    
    sample_data = []
    
    c.executemany('''INSERT INTO plates (plate, name, name2, national_code) VALUES (?, ?, ?, ?)''', sample_data)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    insert_sample_data()

