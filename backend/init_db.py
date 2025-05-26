#!/usr/bin/env python3
"""
Database initialization script for setting up Flask-Migrate and creating tables
"""

import os
import sys
from main import create_app
from database import db
from flask_migrate import init, migrate, upgrade

def init_database():
    """Initialize the database with migrations"""
    app = create_app()
    
    with app.app_context():
        # Check if migrations directory exists
        migrations_dir = 'migrations'
        
        if not os.path.exists(migrations_dir):
            print("Initializing Flask-Migrate...")
            init()
            print("✓ Flask-Migrate initialized")
        
        # Create initial migration
        print("Creating initial migration...")
        migrate(message='Initial migration with photos table')
        print("✓ Initial migration created")
        
        # Apply migration
        print("Applying migrations...")
        upgrade()
        print("✓ Migrations applied successfully")
        
        print("\nDatabase initialization complete!")
        print("Photos table created with columns: id, data, file_type, location, created_at, updated_at")

if __name__ == '__main__':
    init_database() 