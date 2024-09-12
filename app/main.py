import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from fastapi.middleware.cors import CORSMiddleware


# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://terminology-hub.vercel.app"],  # Add the URL of your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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

# Function to create the concepts table
def create_concepts_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            terms TEXT NOT NULL,  -- Stored as a comma-separated string
            preferred_term TEXT,  -- Preferred term for the concept
            status TEXT NOT NULL  -- 'resolved' or 'not resolved'
        )
    ''')
    conn.commit()
    conn.close()

# Function to populate the concepts table with sample data
def populate_concepts_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the table already has data
    cursor.execute("SELECT COUNT(*) FROM concepts")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_data = [
            ("First concept description", "first_term,primary_term", "first_term", "resolved"),
            ("Second concept description", "second_term,secondary_term", "second_term", "resolved"),
            ("Third concept description", "third_term,tertiary_term", None, "not resolved")
        ]
        cursor.executemany('''
            INSERT INTO concepts (description, terms, preferred_term, status)
            VALUES (?, ?, ?, ?)
        ''', sample_data)
        conn.commit()
        print("Sample data inserted into concepts table.")
    else:
        print("Concepts table already populated.")

    conn.close()

# Ensure the table is created and populated on app startup
@app.on_event("startup")
def startup_event():
    create_concepts_table()
    populate_concepts_table()

# Pydantic models for input and output data
class Concept(BaseModel):
    id: int
    description: str
    terms: List[str]
    preferred_term: Optional[str]  # New field for the preferred term
    status: str  # Now "resolved" or "not resolved" depending on the preferred term

class SetPreferredTermRequest(BaseModel):
    preferred_term: str

class UpdateTermsRequest(BaseModel):
    terms: List[str]

# Endpoint to get all concepts
@app.get("/all-concepts", response_model=List[Concept], summary="Retrieve all concepts", description="Fetch all concepts with their descriptions, associated terms, preferred terms, and statuses.")
def get_all_concepts():
    """
    Fetch all concepts stored in the database.

    - **Returns:** A list of all concepts, including their descriptions, associated terms, preferred terms, and status (resolved or not).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM concepts")
    rows = cursor.fetchall()
    conn.close()

    concepts = []
    for row in rows:
        status = "resolved" if row["preferred_term"] else "not resolved"
        concepts.append(Concept(
            id=row["id"],
            description=row["description"],
            terms=row["terms"].split(","),
            preferred_term=row["preferred_term"],  # Return preferred term
            status=status  # Status depends on the preferred term
        ))
    return concepts

# Endpoint to get a specific concept by ID
@app.get("/concept/{concept_id}", response_model=Concept, summary="Retrieve a specific concept by ID", description="Fetch the details of a specific concept by its unique ID, including its description, terms, preferred term, and status.")
def get_concept(concept_id: int):
    """
    Fetch a specific concept by its ID.

    - **concept_id:** The unique ID of the concept to retrieve.
    - **Returns:** The full details of the concept, including its description, terms, preferred term, and status (resolved or not).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM concepts WHERE id = ?", (concept_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        status = "resolved" if row["preferred_term"] else "not resolved"
        return Concept(
            id=row["id"],
            description=row["description"],
            terms=row["terms"].split(","),
            preferred_term=row["preferred_term"],  # Return preferred term
            status=status  # Status depends on the preferred term
        )
    else:
        raise HTTPException(status_code=404, detail="Concept not found")


# Request model for updating status
class UpdateStatusRequest(BaseModel):
    status: str  # The status to update, e.g., "resolved" or "not resolved"

@app.put("/update-status/{concept_name}", response_model=str, summary="Update concept status by name", description="Update the status of a concept by resolving a given name against any associated terms.")
def update_concept_status(concept_name: str, request: UpdateStatusRequest):
    """
    Update the status of a concept by matching its name with the associated terms.

    - **concept_name:** The name or term used to resolve the concept.
    - **status:** The new status for the concept (can be any valid status).
    - **Returns:** A success message indicating the status update.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to find the concept where concept_name matches any of the terms
    cursor.execute("SELECT * FROM concepts WHERE terms LIKE ?", (f"%{concept_name}%",))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Concept not found")

    # Update the concept status
    cursor.execute('''
        UPDATE concepts
        SET status = ?
        WHERE id = ?
    ''', (request.status, row["id"]))

    conn.commit()
    conn.close()

    return f"Concept status updated to {request.status}"

# Endpoint to set the preferred term for a concept
@app.put("/concept/{concept_id}/preferred-term", summary="Set preferred term for a concept", description="Set the preferred term for a specific concept by its ID. The preferred term must be one of the associated terms.")
def set_preferred_term(concept_id: int, request: SetPreferredTermRequest):
    """
    Set the preferred term for a specific concept.

    - **concept_id:** The unique ID of the concept to update.
    - **preferred_term:** The preferred term to set for the concept (must be one of the associated terms).
    - **Returns:** A success message upon completion, and marks the concept as resolved.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the concept exists
    cursor.execute("SELECT * FROM concepts WHERE id = ?", (concept_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Concept not found")

    terms = row["terms"].split(",")
    if request.preferred_term not in terms:
        conn.close()
        raise HTTPException(status_code=400, detail="Preferred term must be one of the terms")

    # Update the concept with the preferred term
    cursor.execute('''
        UPDATE concepts
        SET preferred_term = ?
        WHERE id = ?
    ''', (request.preferred_term, concept_id))

    conn.commit()
    conn.close()

    return {"message": "Preferred term updated successfully"}

# Endpoint to update the terms list for a concept
@app.put("/concept/{concept_id}/update-terms", summary="Update terms for a concept", description="Update the list of terms associated with a specific concept by its ID.")
def update_used_terms(concept_id: int, request: UpdateTermsRequest):
    """
    Update the list of terms associated with a specific concept.

    - **concept_id:** The unique ID of the concept to update.
    - **terms:** The new list of terms to associate with the concept.
    - **Returns:** A success message upon completion.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the concept exists
    cursor.execute("SELECT * FROM concepts WHERE id = ?", (concept_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Concept not found")

    # Update the terms list
    cursor.execute('''
        UPDATE concepts
        SET terms = ?
        WHERE id = ?
    ''', (",".join(request.terms), concept_id))

    conn.commit()
    conn.close()

    return {"message": "Terms updated successfully"}

# Pydantic model for creating a new concept
class CreateConceptRequest(BaseModel):
    description: str
    terms: List[str]
    preferred_term: str  # New field for the preferred term
    status: str

# Endpoint to add a new concept
@app.post("/concepts", response_model=Concept, summary="Add a new concept", description="Add a new concept to the system, providing its description, associated terms, preferred term, and status.")
def add_concept(concept_request: CreateConceptRequest):
    """
    Add a new concept to the system.

    - **description:** A brief description of the concept.
    - **terms:** A list of associated terms for the concept.
    - **preferred_term:** The preferred term for this concept.
    - **status:** Whether the concept is "resolved" or "not resolved".
    - **Returns:** The newly created concept, including its ID, description, terms, preferred term, and status.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert the new concept into the concepts table
    cursor.execute('''
        INSERT INTO concepts (description, terms, preferred_term, status)
        VALUES (?, ?, ?, ?)
    ''', (concept_request.description, ",".join(concept_request.terms), concept_request.preferred_term, concept_request.status))

    # Get the newly created concept ID
    new_concept_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Return the new concept
    return Concept(
        id=new_concept_id,
        description=concept_request.description,
        terms=concept_request.terms,
        preferred_term=concept_request.preferred_term,
        status=concept_request.status
    )
