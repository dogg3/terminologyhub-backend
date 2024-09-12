import sqlite3
import os

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

        # Create the terms table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                all_used_terms TEXT NOT NULL,
                status TEXT NOT NULL
            )
        ''')

        # Sample terms to insert into the database
        sample_data = [
            ("First term description", "first_term,primary_term", "active"),
            ("Second term description", "second_term,secondary_term", "inactive"),
            ("Third term description", "third_term,tertiary_term", "active")
        ]

        # Insert the sample data into the terms table
        cursor.executemany('''
            INSERT INTO terms (description, all_used_terms, status)
            VALUES (?, ?, ?)
        ''', sample_data)

        # Check if the data was inserted successfully
        cursor.execute("SELECT * FROM terms")
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

        print("Database populated with sample terms.")

    except FileNotFoundError as e:
        print(e)
    except sqlite3.Error as db_error:
        print(f"SQLite error occurred: {db_error}")
    except Exception as ex:
        print(f"An error occurred: {ex}")

# Call the function to populate the database
populate_db()
