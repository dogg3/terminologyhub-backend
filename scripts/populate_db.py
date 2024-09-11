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

class NewTermRequest(BaseModel):
    new_term: str

class StatusUpdateRequest(BaseModel):
    status: str  # Either "Resolved" or "Unresolved"

# Example root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Terminology Hub API"}

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

# Endpoint to delete a term from `all_used_terms`
@app.delete("/terms/{term_id}/remove-term/{term}")
def remove_term_from_all_used_terms(term_id: int, term: str):
    conn = get_db_connection()
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

# Endpoint to append a new term to `all_used_terms`
@app.post("/terms/{term_id}/add-term")
def add_term_to_all_used_terms(term_id: int, new_term_request: NewTermRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the term from the database
    cursor.execute("SELECT * FROM terms WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Term not found")

    # Get the current `all_used_terms` as a list
    all_used_terms = row["all_used_terms"].split(",")

    # Check if the new term is already in the list
    if new_term_request.new_term in all_used_terms:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Term '{new_term_request.new_term}' is already in all_used_terms")

    # Append the new term to the list
    all_used_terms.append(new_term_request.new_term)

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

    return {"message": f"Term '{new_term_request.new_term}' added to all_used_terms", "updated_terms": updated_all_used_terms}

# Endpoint to update the status of a term (resolve/unresolve)
@app.post("/terms/{term_id}/update-status")
def update_term_status(term_id: int, status_update: StatusUpdateRequest):
    if status_update.status not in ["Resolved", "Unresolved"]:
        raise HTTPException(status_code=400, detail="Invalid status. Status must be either 'Resolved' or 'Unresolved'.")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the term exists
    cursor.execute("SELECT * FROM terms WHERE id = ?", (term_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Term not found")

    # Update the term's status
    cursor.execute('''
        UPDATE terms
        SET status = ?
        WHERE id = ?
    ''', (status_update.status, term_id))

    conn.commit()
    conn.close()

    return {"message": f"Term status updated to '{status_update.status}'"}
