from flask import request, jsonify
import os
from photo_service import upload_photos_to_db, search_photos


def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "photo-vector-db"})


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


def register_routes(app):
    """Register all routes with the Flask app"""
    app.add_url_rule('/health', 'health_check', health_check, methods=['GET'])
    app.add_url_rule('/upload', 'upload_photos', upload_photos_endpoint, methods=['POST'])
    app.add_url_rule('/search', 'search_photos', search_photos_endpoint, methods=['POST']) 