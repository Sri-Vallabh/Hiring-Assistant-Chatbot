import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('talentscout_candidates.db')
cursor = conn.cursor()

# Create table for storing candidate information
cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email_address TEXT NOT NULL UNIQUE,
            phone_number TEXT NOT NULL,
            years_of_experience INTEGER NOT NULL,
            desired_position TEXT NOT NULL,
            current_location TEXT NOT NULL
        )
    ''')


# Commit changes and close connection
conn.commit()
conn.close()
