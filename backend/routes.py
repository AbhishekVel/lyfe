from flask import request, jsonify
import os
import base64
from datetime import datetime
from photo_service import upload_photos_to_db, search_photos
from models import Photo
from database import db


def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "lyfe-backend"})


def upload_photos_batch():
    """
    Upload a batch of photos to the database
    Expected JSON payload: {
        "photos": [
            {
                "data": "base64_encoded_image_data",
                "location": "location_string",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        if not data or 'photos' not in data:
            return jsonify({"error": "Missing 'photos' field in request body"}), 400
        
        photos = data['photos']
        if not isinstance(photos, list):
            return jsonify({"error": "'photos' must be a list"}), 400
        
        if not photos:
            return jsonify({"error": "Photos list cannot be empty"}), 400
        
        created_photos = []
        errors = []
        
        for i, photo_data in enumerate(photos):
            try:
                # Validate required fields
                if not isinstance(photo_data, dict):
                    errors.append(f"Photo {i}: Must be an object")
                    continue
                
                if 'data' not in photo_data:
                    errors.append(f"Photo {i}: Missing 'data' field")
                    continue
                
                if 'location' not in photo_data:
                    errors.append(f"Photo {i}: Missing 'location' field")
                    continue
                    
                if 'timestamp' not in photo_data:
                    errors.append(f"Photo {i}: Missing 'timestamp' field")
                    continue
                
                base64_data = photo_data['data']
                location = photo_data['location']
                timestamp_str = photo_data['timestamp']
                
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    errors.append(f"Photo {i}: Invalid timestamp format. Use ISO format (e.g., '2024-01-01T12:00:00Z')")
                    continue
                
                # Detect file type from base64 data
                file_type = detect_file_type(base64_data)
                if not file_type:
                    errors.append(f"Photo {i}: Unable to detect file type from base64 data")
                    continue
                
                # Create photo record
                photo = Photo(
                    data=base64_data,
                    file_type=file_type,
                    location=location,
                    created_at=timestamp,
                    updated_at=timestamp
                )
                
                db.session.add(photo)
                created_photos.append({
                    'index': i,
                    'location': location,
                    'timestamp': timestamp_str,
                    'file_type': file_type
                })
                
            except Exception as e:
                errors.append(f"Photo {i}: {str(e)}")
        
        # Commit all successful photos
        if created_photos:
            db.session.commit()
        
        response = {
            "success": len(created_photos) > 0,
            "created_count": len(created_photos),
            "error_count": len(errors),
            "created_photos": created_photos
        }
        
        if errors:
            response["errors"] = errors
        
        status_code = 200 if created_photos else 400
        return jsonify(response), status_code
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to upload photos: {str(e)}"}), 500


def detect_file_type(base64_data):
    """Detect file type from base64 encoded data"""
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:'):
            header, base64_data = base64_data.split(',', 1)
            if 'image/' in header:
                # Extract file type from data URL
                file_type = header.split('image/')[1].split(';')[0]
                return file_type.lower()
        
        # Decode first few bytes to check magic numbers
        decoded_data = base64.b64decode(base64_data[:100])  # Just first few bytes
        
        # Check magic numbers for common image formats
        if decoded_data.startswith(b'\xff\xd8\xff'):
            return 'jpg'
        elif decoded_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        elif decoded_data.startswith(b'GIF8'):
            return 'gif'
        elif decoded_data.startswith(b'RIFF') and b'WEBP' in decoded_data[:20]:
            return 'webp'
        elif decoded_data.startswith(b'BM'):
            return 'bmp'
        else:
            # Default to jpg if unknown
            return 'jpg'
            
    except Exception:
        return 'jpg'  # Default fallback


def upload_photos_endpoint():
    """
    Upload photos from a directory to the vector database
    Expected JSON payload: {"directory": "/path/to/photos"}
    """
    try:
        data = request.get_json()
        if not data or 'directory' not in data:
            return jsonify({"error": "Missing 'directory' field in request body"}), 400
        
        directory = data['directory']
        
        # Validate directory exists
        if not os.path.exists(directory):
            return jsonify({"error": f"Directory '{directory}' does not exist"}), 400
        
        if not os.path.isdir(directory):
            return jsonify({"error": f"Path '{directory}' is not a directory"}), 400
        
        # Process photos
        result = upload_photos_to_db(directory)
        
        return jsonify({
            "success": True,
            "message": f"Processed {result['processed']} out of {result['total_found']} photos",
            "details": result
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to upload photos: {str(e)}"}), 500


def search_photos_endpoint():
    """
    Search for photos using a text query
    Expected JSON payload: {"query": "search text"}
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' field in request body"}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400
        
        # Search photos
        matches = search_photos(query)
        
        return jsonify({
            "success": True,
            "query": query,
            "matches": matches,
            "count": len(matches)
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to search photos: {str(e)}"}), 500


def get_photos_endpoint():
    """
    Get all photos from the database with optional pagination
    Query parameters: limit, offset
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            return jsonify({"error": "Limit must be between 1 and 1000"}), 400
        
        if offset < 0:
            return jsonify({"error": "Offset must be non-negative"}), 400
        
        # Query photos
        photos = Photo.query.offset(offset).limit(limit).all()
        total_count = Photo.query.count()
        
        return jsonify({
            "success": True,
            "photos": [photo.to_dict() for photo in photos],
            "pagination": {
                "offset": offset,
                "limit": limit,
                "total": total_count,
                "returned": len(photos)
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get photos: {str(e)}"}), 500


def register_routes(app):
    """Register all routes with the Flask app"""
    app.add_url_rule('/health', 'health_check', health_check, methods=['GET'])
    app.add_url_rule('/upload_photos', 'upload_photos_batch', upload_photos_batch, methods=['POST'])
    app.add_url_rule('/upload', 'upload_photos', upload_photos_endpoint, methods=['POST'])
    app.add_url_rule('/search', 'search_photos', search_photos_endpoint, methods=['POST'])
    app.add_url_rule('/photos', 'get_photos', get_photos_endpoint, methods=['GET']) 