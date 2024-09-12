import sqlite3
import os
from random import randint


# Function to populate the database with sample data
def populate_db():
    db_path = "./tmp/terminology_hub.db"  # Change this to your local db path if needed
    print(f"Connecting to database at {db_path}")

    try:
        # Check if the file exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Error: Database file not found at {db_path}")

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the concepts table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                terms TEXT NOT NULL,  -- Stored as a comma-separated string
                preferred_term TEXT,  -- Preferred term for the concept
                status TEXT NOT NULL  -- 'resolved' or 'not resolved'
            )
        ''')

        # Sample concepts to insert into the database
        sample_data = [
            ("First concept description", "first_term,primary_term", "first_term", "resolved"),
            ("Second concept description", "second_term,secondary_term", "second_term", "resolved"),
            ("Third concept description", "third_term,tertiary_term", None, "not resolved"),
            ("Fourth concept description", "fourth_term,quaternary_term", "fourth_term", "resolved"),
            ("Fifth concept description", "fifth_term,quinary_term", None, "not resolved"),
            ("Sixth concept description", "sixth_term,senary_term", "sixth_term", "resolved"),
            ("Seventh concept description", "seventh_term,septenary_term", None, "not resolved"),
            ("Eighth concept description", "eighth_term,octonary_term", "octonary_term", "resolved"),
            ("Ninth concept description", "ninth_term,nonary_term", None, "not resolved"),
            ("Tenth concept description", "tenth_term,denary_term", "tenth_term", "resolved")
        ]

        # Insert the sample data into the concepts table
        cursor.executemany('''
            INSERT INTO concepts (description, terms, preferred_term, status)
            VALUES (?, ?, ?, ?)
        ''', sample_data)

        # Check if the data was inserted successfully
        cursor.execute("SELECT * FROM concepts")
        rows = cursor.fetchall()

        if rows:
            print("Sample data inserted successfully:")
            for row in rows:
                print(row)
        else:
            print("No data found after insertion.")

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        print("Database populated with sample concepts.")

    except FileNotFoundError as e:
        print(e)
    except sqlite3.Error as db_error:
        print(f"SQLite error occurred: {db_error}")
    except Exception as ex:
        print(f"An error occurred: {ex}")


# Call the function to populate the database
populate_db()
