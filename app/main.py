import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3

# Initialize FastAPI app
app = FastAPI()

# Function to get a database connection
def get_db_connection():
    try:
        db_path = "/tmp/terminology_hub.db"
        print(f"Connecting to database at: {os.path.abspath(db_path)}")  # Print the full path for debugging
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Function to create the terms table
def create_terms_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            all_used_terms TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Function to populate the terms table with sample data
def populate_terms_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the table already has data
    cursor.execute("SELECT COUNT(*) FROM terms")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_data = [
            ("First term description", "first_term,primary_term", "active"),
            ("Second term description", "second_term,secondary_term", "inactive"),
            ("Third term description", "third_term,tertiary_term", "active")
        ]
        cursor.executemany('''
            INSERT INTO terms (description, all_used_terms, status)
            VALUES (?, ?, ?)
        ''', sample_data)
        conn.commit()
        print("Sample data inserted into terms table.")
    else:
        print("Terms table already populated.")

    conn.close()

# Ensure the table is created and populated on app startup
@app.on_event("startup")
def startup_event():
    create_terms_table()
    populate_terms_table()

# Pydantic models for input and output data
class Term(BaseModel):
    id: int
    description: str
    all_used_terms: List[str]
    status: str

class ResolveRequest(BaseModel):
    preferred_term: str
    description: str

# Root endpoint
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Endpoint to get all terms
@app.get("/terms", response_model=List[Term])
def get_all_terms():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms")
    rows = cursor.fetchall()
    conn.close()

    terms = []
    for row in rows:
        terms.append(Term(
            id=row["id"],
            description=row["description"],
            all_used_terms=row["all_used_terms"].split(","),
            status=row["status"]
        ))
    return terms

# Endpoint to get a specific term by ID
@app.get("/terms/{term_id}", response_model=Term)
def get_term(term_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms WHERE id = ?", (term_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return Term(
            id=row["id"],
            description=row["description"],
            all_used_terms=row["all_used_terms"].split(","),
            status=row["status"]
        )
    else:
        raise HTTPException(status_code=404, detail="Term not found")

# Endpoint to resolve a term by updating its status and preferred term
@app.post("/terms/{term_id}/resolve")
def resolve_term(term_id: int, resolve_request: ResolveRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the term exists
    cursor.execute("SELECT * FROM terms WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Term not found")

    # Update the term with the preferred term and description
    all_used_terms = resolve_request.preferred_term
    cursor.execute('''
        UPDATE terms
        SET description = ?, all_used_terms = ?, status = "Resolved"
        WHERE id = ?
    ''', (resolve_request.description, all_used_terms, term_id))

    conn.commit()
    conn.close()

    return {"message": "Term resolved successfully"}
