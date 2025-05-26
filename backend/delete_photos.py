#!/usr/bin/env python3
"""
Script to delete all rows from the photos table in the PostgreSQL database
and all vectors from the Pinecone vector database.
"""

import os
import sys
from main import create_app
from models import Photo
from database import db
from photo_service import get_vector_count_in_namespace, delete_all_vectors_from_namespace
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_all_photos():
    """Delete all rows from the photos table and all vectors from Pinecone"""
    # Override DATABASE_URL to connect to localhost (for running outside Docker)
    os.environ['DATABASE_URL'] = 'postgresql://postgres:password123@localhost:5432/lyfe'
    
    app = create_app()
    
    with app.app_context():
        try:
            # Count existing photos in PostgreSQL
            count_before = Photo.query.count()
            print(f"Found {count_before} photos in the PostgreSQL database")
            
            # Get vector count from Pinecone namespace
            print("🔍 Checking Pinecone vector count...")
            success, vector_info = get_vector_count_in_namespace()
            if success:
                vector_count = vector_info
                print(f"Found {vector_count} vectors in Pinecone namespace")
            else:
                print(f"⚠️  Warning: Could not get Pinecone vector count: {vector_info}")
                vector_count = "unknown"
            
            if count_before == 0 and (vector_count == 0 or vector_count == "unknown"):
                print("No photos to delete from PostgreSQL" + (" and no vectors in Pinecone." if vector_count == 0 else "."))
                return
            
            # Confirm deletion
            print(f"⚠️  WARNING: This will delete:")
            print(f"   - ALL {count_before} photos from PostgreSQL database")
            if vector_count != "unknown":
                print(f"   - ALL {vector_count} vectors from Pinecone namespace")
            else:
                print(f"   - ALL vectors from Pinecone namespace (count unknown)")
            print("This action cannot be undone.")
            
            user_input = input("Are you sure you want to continue? (y/N): ")
            if user_input.lower() not in ['y', 'yes']:
                print("❌ Deletion cancelled by user.")
                return
            
            # Delete all vectors from Pinecone namespace first
            print("🗑️  Deleting vectors from Pinecone...")
            success, result = delete_all_vectors_from_namespace()
            if success:
                print(f"✅ Successfully deleted all vectors from Pinecone namespace")
            else:
                print(f"❌ Error deleting vectors from Pinecone: {result}")
                print("⚠️  Continuing with PostgreSQL deletion...")
            
            # Delete all photos from PostgreSQL
            print("🗑️  Deleting photos from PostgreSQL...")
            deleted_count = Photo.query.delete()
            db.session.commit()
            
            print(f"✅ Successfully deleted {deleted_count} photos from PostgreSQL database")
            
            # Verify deletion
            count_after = Photo.query.count()
            print(f"Photos remaining in PostgreSQL: {count_after}")
            
            print("🎉 Deletion completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during deletion: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    delete_all_photos() 