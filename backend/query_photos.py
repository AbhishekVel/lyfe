#!/usr/bin/env python3
"""
Script to query all photos from the database
"""
import os
from main import create_app
from models import Photo

def query_all_photos():
    """Query and display all photos from the database"""
    # Use the Docker PostgreSQL database URL
    os.environ['DATABASE_URL'] = 'postgresql://postgres:password123@localhost:5432/lyfe'
    
    app = create_app()
    
    with app.app_context():
        try:
            # Query all photos
            photos = Photo.query.all()
            
            print(f"Found {len(photos)} photos in the database:\n")
            
            if not photos:
                print("No photos found in the database.")
                return
            
            # Display photo information
            for i, photo in enumerate(photos, 1):
                print(f"Photo {i}:")
                print(f"  ID: {photo.id}")
                print(f"  File Type: {photo.file_type}")
                print(f"  Path: {photo.path}")
                print(f"  Location: {photo.location or 'Not specified'}")
                print(f"  Timestamp: {photo.timestamp or 'Not specified'}")
                print(f"  Data Length: {len(photo.data) if photo.data else 0} characters")
                print("-" * 50)
                
        except Exception as e:
            print(f"Error querying photos: {e}")
            return False

if __name__ == "__main__":
    query_all_photos() 