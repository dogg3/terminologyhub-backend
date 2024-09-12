from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3

# Function to populate the database with sample data
def populate_db():
    # Connect to the database
    conn = sqlite3.connect("terminology_hub.db")
    cursor = conn.cursor()

    # Fetch the term from the database
    cursor.execute("SELECT * FROM terms WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Term not found")

    # Get the `all_used_terms` as a list
    all_used_terms = row["all_used_terms"].split(",")

    # Check if the term exists in the list
    if term not in all_used_terms:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Term '{term}' not found in all_used_terms")

    # Remove the specified term
    all_used_terms.remove(term)

    # Convert the list back to a comma-separated string
    updated_all_used_terms = ",".join(all_used_terms)

    # Update the database
    cursor.execute('''
        UPDATE terms
        SET all_used_terms = ?
        WHERE id = ?
    ''', (updated_all_used_terms, term_id))

    conn.commit()
    conn.close()

    return {"message": f"Term '{term}' removed from all_used_terms", "updated_terms": updated_all_used_terms}

