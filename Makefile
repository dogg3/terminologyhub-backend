# Variables
DB_FILE=terminology_hub.db
MIGRATION_DIR=migrations
POPULATE_SCRIPT=scripts/populate_db.py
UVICORN_CMD=uvicorn app.main:app --reload

# Default target
all: help

# Help target to list available commands
help:
	@echo "Available commands:"
	@echo "  make initdb   - Initialize the database and run migrations"
	@echo "  make run      - Run the FastAPI server"
	@echo "  make populate - Populate the database with sample data"
	@echo "  make clean    - Delete the database file"

# Initialize the database
initdb:
	@echo "Initializing the database..."
	@sqlite3 $(DB_FILE) < $(MIGRATION_DIR)/001_create_terms_table.sql
	@echo "Database initialized."

# Populate the database with sample data
populate:
	@echo "Populating the database with sample data..."
	@python3 $(POPULATE_SCRIPT)
	@echo "Database populated."

# Run the FastAPI application
run:
	@echo "Starting FastAPI server..."
	@$(UVICORN_CMD)

# Clean up the database
clean:
	@echo "Deleting the database..."
	@rm -f $(DB_FILE)
	@echo "Database deleted."
