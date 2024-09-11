-- Create the `terms` table
CREATE TABLE IF NOT EXISTS terms (
                                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                                     description TEXT NOT NULL,
                                     all_used_terms TEXT NOT NULL,  -- Stored as a comma-separated string
                                     status TEXT NOT NULL
);
