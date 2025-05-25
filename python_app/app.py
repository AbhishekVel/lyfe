from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pathlib import Path
from typing import List, Optional
from PIL import Image as PILImage
from io import BytesIO
from tqdm import tqdm
import vertexai
from vertexai.vision_models import Image as VertexImage, MultiModalEmbeddingModel
from pinecone import Pinecone
from constants import LOCATION_NAMESPACE, PHOTOS_INDEX_NAME, PHOTOS_NAMESPACE, VECTOR_DIMENSION

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize services
vertexai.init(project=os.getenv("GCP_PROJECT_ID"), location="us-central1")
model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def find_photos_in_dir(dir: str) -> List[str]:
    photo_files = []
    for root, _, files in os.walk(dir):
        for file in files:
            if file.lower().endswith("png"):
                photo_files.append(str((Path(root) / file).absolute()))
    return photo_files


def get_resized_image_bytes(path: str) -> bytes:
    """Resize image to 512px width maintaining aspect ratio and return as bytes."""
    with PILImage.open(path) as img:
        # Calculate height to maintain aspect ratio
        width = 512
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio)

        # Resize image
        resized_img = img.resize((width, height))

        # Convert to bytes
        img_byte_arr = BytesIO()
        resized_img.save(img_byte_arr, format=img.format)
        return img_byte_arr.getvalue()


def gen_image_embedding(path: str):
    image = VertexImage(image_bytes=get_resized_image_bytes(path))
    embeddings = model.get_embeddings(
        image=image,
        dimension=VECTOR_DIMENSION,
    )
    return embeddings.image_embedding


def get_gps_coords_from_image(path: str) -> Optional[tuple[float, float]]:
    try:
        from PIL.ExifTags import GPSTAGS
        from PIL.ExifTags import TAGS
        
        with PILImage.open(path) as img:
            # Get EXIF data
            exif = img._getexif()
            if not exif:
                return None
                
            # Get GPS info
            for tag_id in exif:
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    gps_data = {}
                    for gps_tag in exif[tag_id]:
                        gps_data[GPSTAGS.get(gps_tag, gps_tag)] = exif[tag_id][gps_tag]
                    
                    if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
                        # Get direction indicators
                        lat_ref = gps_data.get("GPSLatitudeRef", "N")
                        lon_ref = gps_data.get("GPSLongitudeRef", "E")
                        
                        # Calculate decimal degrees
                        latitude = gps_data["GPSLatitude"][0] + gps_data["GPSLatitude"][1] / 60.0 + gps_data["GPSLatitude"][2] / 3600.0
                        longitude = gps_data["GPSLongitude"][0] + gps_data["GPSLongitude"][1] / 60.0 + gps_data["GPSLongitude"][2] / 3600.0
                        
                        # Apply direction
                        if lat_ref == "S":
                            latitude = -latitude
                        if lon_ref == "W":
                            longitude = -longitude
                            
                        return (latitude, longitude)
            
            return None
    except:
        return None


def get_image_location(path: str) -> Optional[str]:
    gps_coords = get_gps_coords_from_image(path)
    if not gps_coords:
        return None
    # use geopy to get the location name from the gps coords
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="abhi-agent")
    location = geolocator.reverse(gps_coords)
    if not location:
        return None
    return location.address


def gen_text_embedding(text: str) -> list[float]:
    embeddings = model.get_embeddings(
        contextual_text=text,
        dimension=VECTOR_DIMENSION,
    )
    return embeddings.text_embedding


def exists_in_index(path: str, namespace: str) -> bool:
    index = pc.Index(PHOTOS_INDEX_NAME)
    return bool(index.fetch(
        ids=[path], namespace=namespace
    ).vectors)


def update_index(path: str, embedding: list[float], namespace: str):
    index = pc.Index(PHOTOS_INDEX_NAME)
    index.upsert(
        vectors=[
            {
                "id": path,
                "values": embedding,
                "metadata": {
                    "path": path,
                },
            },
        ],
        namespace=namespace,
    )


def gen_caption_embedding(path: str) -> Optional[list[float]]:
    # At the moment, we're just using the location as the caption
    location = get_image_location(path)
    if not location:
        return None
    return gen_text_embedding(location)


def upload_photos_to_db(dir: str):
    """Process photos in directory and upload to vector database"""
    photos = find_photos_in_dir(dir)
    if not photos:
        return {"error": "No PNG photos found in directory", "processed": 0}
    
    processed = 0
    errors = []
    
    for path in tqdm(photos, desc="Processing photos"):
        try:
            # First check to see if the image is already in the index
            if not exists_in_index(path, PHOTOS_NAMESPACE):
                image_embedding = gen_image_embedding(path)
                update_index(path=path, embedding=image_embedding, namespace=PHOTOS_NAMESPACE)
            
            if not exists_in_index(path, LOCATION_NAMESPACE):
                caption_embedding = gen_caption_embedding(path)
                if caption_embedding:
                    update_index(path=path, embedding=caption_embedding, namespace=LOCATION_NAMESPACE)
            
            processed += 1
        except Exception as e:
            errors.append(f"Error processing photo {path}: {str(e)}")
            continue
    
    return {
        "processed": processed,
        "total_found": len(photos),
        "errors": errors
    }


def search_photos(query: str):
    """Search for photos using text query"""
    try:
        # Generate embedding for search query
        query_embedding = gen_text_embedding(query)

        # Search pinecone index
        index = pc.Index(PHOTOS_INDEX_NAME)
        search_results = index.query(
            vector=query_embedding, top_k=20, namespace=PHOTOS_NAMESPACE
        )

        # TOOD: also search location namespace
        print(search_results)
        # Return paths of matching photos
        matches = []
        for match in search_results.matches:
            matches.append({
                "path": match.id,
                "score": match.score,
                "metadata": match.metadata
            })

        return matches
    except Exception as e:
        raise Exception(f"Error searching photos: {str(e)}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "photo-vector-db"})


@app.route('/upload', methods=['POST'])
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


@app.route('/search', methods=['POST'])
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


if __name__ == '__main__':
    # Check required environment variables
    required_env_vars = ["GCP_PROJECT_ID", "PINECONE_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=7100) 