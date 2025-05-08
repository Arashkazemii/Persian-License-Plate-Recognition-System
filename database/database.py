import sqlite3

def create_database():
    conn = sqlite3.connect('./database/plates.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS plates (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              name TEXT, 
              name2 TEXT, 
              plate TEXT, 
              time_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
