#!/usr/bin/env python3
"""
Script to create Flask-Migrate migrations
"""
import sys
import os
from flask_migrate import migrate as flask_migrate, upgrade
from main import create_app

def create_migration(message=None):
    """Create a new migration"""
    # Use the actual database URL - PostgreSQL running in Docker
    os.environ['DATABASE_URL'] = 'postgresql://postgres:password123@localhost:5432/lyfe'
    
    app = create_app()
    
    with app.app_context():
        try:
            if message is None:
                message = "Auto-generated migration"
            
            print("Upgrading database to latest migration...")
            # First, upgrade to the latest migration
            upgrade()
            
            print("Creating new migration...")
            # Generate migration
            flask_migrate(message=message)
            print(f"Migration created successfully with message: '{message}'")
            
        except Exception as e:
            print(f"Error creating migration: {e}")
            return False
    
    return True

if __name__ == "__main__":
    # Get message from command line arguments or use default
    message = sys.argv[1] if len(sys.argv) > 1 else "Update Photo model schema"
    create_migration(message) 