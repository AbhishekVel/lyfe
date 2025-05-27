from flask import request, jsonify
import os
import base64
from datetime import datetime
from photo_service import search_photos, gen_image_embedding_from_base64, update_index_with_photo_id, exists_in_index_by_photo_id, get_vector_count_in_namespace, delete_all_vectors_from_namespace
from models import Photo
from database import db
from chat import run_chat, Message, TextInput
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        vector_processing_errors = []
        
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
                
                # Create photo record in PostgreSQL first
                photo = Photo(
                    data=base64_data,
                    file_type=file_type,
                    location=location,
                    created_at=timestamp,
                    updated_at=timestamp
                )
                
                db.session.add(photo)
                db.session.flush()  # Flush to get the photo ID without committing
                
                # Now we have the photo ID, attempt vector processing
                try:
                    # Check if vector already exists for this photo ID
                    if not exists_in_index_by_photo_id(str(photo.id)):
                        # Generate embedding from base64 data
                        image_embedding = gen_image_embedding_from_base64(base64_data)
                        logger.info(f"Successfully generated embedding for photo ID {photo.id}")
                        
                        # Store vector in Pinecone using photo ID
                        update_index_with_photo_id(
                            photo_id=str(photo.id), 
                            embedding=image_embedding
                        )
                        logger.info(f"Successfully stored vector in Pinecone for photo ID {photo.id}")
                    else:
                        logger.info(f"Vector already exists in Pinecone for photo ID {photo.id}, skipping")
                    
                except Exception as vector_error:
                    # Log vector processing error but don't fail the photo upload
                    error_msg = f"Photo {i} (ID: {photo.id}): Vector processing failed - {str(vector_error)}"
                    vector_processing_errors.append(error_msg)
                    logger.error(error_msg)
                
                created_photos.append({
                    'index': i,
                    'id': photo.id,
                    'location': location,
                    'timestamp': timestamp_str,
                    'file_type': file_type
                })
                
            except Exception as e:
                errors.append(f"Photo {i}: {str(e)}")
                db.session.rollback()
                continue
        
        # Commit all successful photos
        if created_photos:
            db.session.commit()
            logger.info(f"Successfully uploaded {len(created_photos)} photos to PostgreSQL")
        
        response = {
            "success": len(created_photos) > 0,
            "created_count": len(created_photos),
            "error_count": len(errors),
            "vector_processing_error_count": len(vector_processing_errors),
            "created_photos": created_photos
        }
        
        if errors:
            response["errors"] = errors
        
        if vector_processing_errors:
            response["vector_processing_errors"] = vector_processing_errors
        
        status_code = 200 if created_photos else 400
        return jsonify(response), status_code
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to upload photos: {str(e)}")
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



# def search_photos_endpoint():
#     """
#     Search for photos using a text query
#     Expected JSON payload: {"query": "search text"}
#     Returns complete Photo objects from PostgreSQL based on vector search results
#     """
#     try:
#         data = request.get_json()
#         if not data or 'query' not in data:
#             return jsonify({"error": "Missing 'query' field in request body"}), 400
        
#         query = data['query'].strip()
#         if not query:
#             return jsonify({"error": "Query cannot be empty"}), 400
        
#         # Search photos - now returns complete Photo objects
#         search_results = search_photos(query)
        
#         return jsonify({
#             "success": True,
#             "query": query,
#             "results": search_results,
#             "count": len(search_results)
#         })
        
#     except Exception as e:
#         logger.error(f"Failed to search photos: {str(e)}")
#         return jsonify({"error": f"Failed to search photos: {str(e)}"}), 500


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


def delete_all_data_endpoint():
    """
    Delete all photos from PostgreSQL database and all vectors from Pinecone namespace
    This is a destructive operation that cannot be undone.
    """
    try:
        # Check if request includes confirmation
        data = request.get_json() or {}
        confirmed = data.get('confirmed', False)
        
        if not confirmed:
            # Return counts for confirmation
            photo_count = Photo.query.count()
            success, vector_info = get_vector_count_in_namespace()
            vector_count = vector_info if success else "unknown"
            
            return jsonify({
                "success": False,
                "message": "Confirmation required. This will delete all data permanently.",
                "data_to_delete": {
                    "postgresql_photos": photo_count,
                    "pinecone_vectors": vector_count
                },
                "confirmation_required": True,
                "note": "Send POST request with {'confirmed': true} to proceed"
            }), 200
        
        # Proceed with deletion
        logger.info("Starting delete_all_data operation")
        
        # Get initial counts
        photo_count_before = Photo.query.count()
        success, vector_info = get_vector_count_in_namespace()
        vector_count_before = vector_info if success else 0
        
        logger.info(f"Found {photo_count_before} photos in PostgreSQL and {vector_count_before} vectors in Pinecone")
        
        deletion_results = {
            "postgresql": {"before": photo_count_before, "deleted": 0, "success": False, "error": None},
            "pinecone": {"before": vector_count_before, "success": False, "error": None}
        }
        
        # Delete vectors from Pinecone first
        logger.info("Deleting vectors from Pinecone...")
        pinecone_success, pinecone_result = delete_all_vectors_from_namespace()
        deletion_results["pinecone"]["success"] = pinecone_success
        if not pinecone_success:
            deletion_results["pinecone"]["error"] = pinecone_result
            logger.error(f"Pinecone deletion failed: {pinecone_result}")
        else:
            logger.info("Successfully deleted vectors from Pinecone")
        
        # Delete photos from PostgreSQL
        logger.info("Deleting photos from PostgreSQL...")
        try:
            deleted_count = Photo.query.delete()
            db.session.commit()
            deletion_results["postgresql"]["deleted"] = deleted_count
            deletion_results["postgresql"]["success"] = True
            logger.info(f"Successfully deleted {deleted_count} photos from PostgreSQL")
        except Exception as e:
            db.session.rollback()
            deletion_results["postgresql"]["error"] = str(e)
            logger.error(f"PostgreSQL deletion failed: {str(e)}")
        
        # Verify deletions
        photo_count_after = Photo.query.count()
        
        # Determine overall success
        overall_success = deletion_results["postgresql"]["success"] and deletion_results["pinecone"]["success"]
        
        response = {
            "success": overall_success,
            "message": "Data deletion completed" if overall_success else "Data deletion completed with some errors",
            "results": deletion_results,
            "verification": {
                "postgresql_photos_remaining": photo_count_after
            }
        }
        
        status_code = 200 if overall_success else 207  # 207 Multi-Status for partial success
        return jsonify(response), status_code
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete all data: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to delete all data: {str(e)}"
        }), 500


def chat_endpoint():
    logger.info("Chat endpoint called")
    try:
        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({"error": "Missing 'messages' field in request body"}), 400
        
        logger.info(f"Data: {data}")
        
        messages_data = data['messages']
        if not isinstance(messages_data, list):
            return jsonify({"error": "'messages' must be a list"}), 400
        
        if not messages_data:
            return jsonify({"error": "Messages list cannot be empty"}), 400
        
        # Convert dict messages to Message objects
        messages = []
        for msg_data in messages_data:
            try:
                message = Message.from_dict(msg_data)
                messages.append(message)
            except Exception as e:
                return jsonify({"error": f"Invalid message format: {str(e)}"}), 400
        
        # Run the chat and get response
        response = run_chat(messages)
        
        if response is None:
            return jsonify({"error": "Failed to get response from chat service"}), 500
        
        # Convert response to Message format
        response_message = Message(
            role="assistant", 
            content=[TextInput(text=response.get_message() or "")]
        )
        
        return jsonify({
            "success": True,
            "response": response_message.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to process chat: {str(e)}")
        return jsonify({"error": f"Failed to process chat: {str(e)}"}), 500


def register_routes(app):
    """Register all routes with the Flask app"""
    app.add_url_rule('/health', 'health_check', health_check, methods=['GET'])
    app.add_url_rule('/upload_photos', 'upload_photos_batch', upload_photos_batch, methods=['POST'])
    app.add_url_rule('/photos', 'get_photos', get_photos_endpoint, methods=['GET'])
    # app.add_url_rule('/search', 'search_photos', search_photos_endpoint, methods=['POST'])
    app.add_url_rule('/delete_all_data', 'delete_all_data', delete_all_data_endpoint, methods=['POST', 'DELETE'])
    app.add_url_rule('/chat', 'chat', chat_endpoint, methods=['POST']) 