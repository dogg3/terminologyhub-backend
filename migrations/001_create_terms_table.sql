-- Create the `concepts` table
CREATE TABLE IF NOT EXISTS concepts (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        description TEXT NOT NULL,
                                        terms TEXT NOT NULL,  -- Stored as a comma-separated string
                                        preferred_term TEXT,  -- Preferred term for the concept
                                        status TEXT NOT NULL  -- 'resolved' or 'not resolved'
);
