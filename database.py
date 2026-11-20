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
def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Departments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT UNIQUE NOT NULL
        )
    """)

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL,
            default_priority TEXT NOT NULL
        )
    """)

    # Complaints table
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # Complaint history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            note TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id)
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