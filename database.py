import sqlite3
import os

# Database file location
DATABASE_PATH = "instance/campuscare.db"


# Connect to database
def get_connection():

    os.makedirs("instance", exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    return connection


# Create database tables
# Create database tables
def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL,
            default_priority TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            assigned_staff INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            note TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()

    print("Database tables created successfully!")
    
    


# Add default departments and categories
def insert_default_data():

    connection = get_connection()
    cursor = connection.cursor()

    departments = [
        "Computer Science",
        "Electrical",
        "Mechanical",
        "Civil",
        "Administration",
        "Housekeeping"
    ]

    for department in departments:
        cursor.execute("""
            INSERT OR IGNORE INTO departments (department_name)
            VALUES (?)
        """, (department,))

    categories = [
        ("Electrical", "High"),
        ("Water Supply", "High"),
        ("Internet / Wi-Fi", "Medium"),
        ("Cleanliness", "Medium"),
        ("Furniture", "Low"),
        ("Classroom Equipment", "Medium"),
        ("Other", "Low")
    ]

    for category, priority in categories:
        cursor.execute("""
            INSERT OR IGNORE INTO categories
            (category_name, default_priority)
            VALUES (?, ?)
        """, (category, priority))

    connection.commit()
    connection.close()

    print("Default data added successfully!")


# Run database setup
def initialize_database():

    create_tables()
    insert_default_data()


if __name__ == "__main__":

    initialize_database()