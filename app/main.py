from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3

# Initialize FastAPI app
app = FastAPI()

# Define the database connection function
def get_db_connection():
    conn = sqlite3.connect("terminology_hub.db")  # Path to your SQLite DB
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

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
