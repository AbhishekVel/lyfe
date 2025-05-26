#!/usr/bin/env python3
"""
Script to apply Flask-Migrate migrations
"""
import os
from flask_migrate import upgrade
from main import create_app

def apply_migrations():
    """Apply all pending migrations"""
    # Use the actual database URL - PostgreSQL running in Docker
    os.environ['DATABASE_URL'] = 'postgresql://postgres:password123@localhost:5432/lyfe'
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Applying migrations...")
            upgrade()
            print("All migrations applied successfully!")
            
        except Exception as e:
            print(f"Error applying migrations: {e}")
            return False
    
    return True

if __name__ == "__main__":
    apply_migrations() 