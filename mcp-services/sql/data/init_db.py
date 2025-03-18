import sqlite3

# Create a connection to the database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    salary REAL NOT NULL,
    hire_date TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    budget REAL NOT NULL,
    location TEXT NOT NULL
)
''')

# Insert sample data
employees = [
    (1, 'John Doe', 'Engineering', 85000.00, '2020-01-15'),
    (2, 'Jane Smith', 'Marketing', 75000.00, '2019-05-20'),
    (3, 'Bob Johnson', 'Engineering', 90000.00, '2018-11-10'),
    (4, 'Alice Williams', 'HR', 65000.00, '2021-03-05'),
    (5, 'Charlie Brown', 'Finance', 95000.00, '2017-08-22'),
    (6, 'Diana Miller', 'Marketing', 78000.00, '2020-09-14'),
    (7, 'Edward Davis', 'Engineering', 88000.00, '2019-02-28'),
    (8, 'Fiona Clark', 'HR', 67000.00, '2021-07-19'),
    (9, 'George Wilson', 'Finance', 92000.00, '2018-04-11'),
    (10, 'Hannah Moore', 'Engineering', 86000.00, '2020-11-30')
]

departments = [
    (1, 'Engineering', 1500000.00, 'Building A'),
    (2, 'Marketing', 800000.00, 'Building B'),
    (3, 'HR', 400000.00, 'Building A'),
    (4, 'Finance', 1200000.00, 'Building C')
]

cursor.executemany('INSERT OR REPLACE INTO employees VALUES (?, ?, ?, ?, ?)', employees)
cursor.executemany('INSERT OR REPLACE INTO departments VALUES (?, ?, ?, ?)', departments)

# Commit changes and close connection
conn.commit()
conn.close()

print("Database initialized with sample data.")
