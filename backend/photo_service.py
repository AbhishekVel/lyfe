import os
from models import Photo
from database import db
import base64
import logging
from pathlib import Path
from typing import List, Optional
from PIL import Image as PILImage
from PIL.ExifTags import GPSTAGS
from PIL.ExifTags import TAGS
from io import BytesIO
from tqdm import tqdm
import vertexai
from vertexai.vision_models import Image as VertexImage, MultiModalEmbeddingModel
from pinecone import Pinecone
from constants import LOCATION_NAMESPACE, PHOTOS_INDEX_NAME, PHOTOS_NAMESPACE, VECTOR_DIMENSION

# Set up logging
logger = logging.getLogger(__name__)

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


def resize_to_square(image: PILImage.Image, size: int = 512) -> PILImage.Image:
    """
    Resize image to square format without cropping.
    
    Args:
        image: PIL Image object
        size: Target size for square image (default: 512)
        
    Returns:
        PIL Image object resized to square format
    """
    # Simply resize to target size (will stretch/distort if not square)
    resized_image = image.resize((size, size), PILImage.Resampling.LANCZOS)
    
    return resized_image


def get_resized_image_bytes(path: str) -> bytes:
    """Resize image to 512x512 square format and return as bytes."""
    with PILImage.open(path) as img:
        # Resize to square format
        resized_img = resize_to_square(img, 512)

        # Convert to bytes
        img_byte_arr = BytesIO()
        resized_img.save(img_byte_arr, format=img.format)
        return img_byte_arr.getvalue()


def get_resized_image_bytes_from_base64(base64_data: str) -> bytes:
    """Resize image from base64 data to 512x512 square format and return as bytes."""
    # Remove data URL prefix if present
    if base64_data.startswith('data:'):
        _, base64_data = base64_data.split(',', 1)
    
    # Decode base64 data
    image_data = base64.b64decode(base64_data)
    
    # Open image from bytes
    with PILImage.open(BytesIO(image_data)) as img:
        # Resize to square format
        resized_img = resize_to_square(img, 512)

        # Convert to bytes
        img_byte_arr = BytesIO()
        # Use PNG format for consistency
        resized_img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()


def gen_image_embedding(path: str):
    image = VertexImage(image_bytes=get_resized_image_bytes(path))
    embeddings = model.get_embeddings(
        image=image,
        dimension=VECTOR_DIMENSION,
    )
    return embeddings.image_embedding


def gen_image_embedding_from_base64(base64_data: str):
    """Generate image embedding from base64 encoded image data."""
    image_bytes = get_resized_image_bytes_from_base64(base64_data)
    image = VertexImage(image_bytes=image_bytes)
    embeddings = model.get_embeddings(
        image=image,
        dimension=VECTOR_DIMENSION,
    )
    return embeddings.image_embedding


def get_gps_coords_from_image(path: str) -> Optional[tuple[float, float]]:
    try:
        
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


def exists_in_index_by_photo_id(photo_id: str) -> bool:
    """Check if vector exists in Pinecone index using PostgreSQL photo ID."""
    index = pc.Index(PHOTOS_INDEX_NAME)
    return bool(index.fetch(
        ids=[photo_id], namespace=PHOTOS_NAMESPACE
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


def update_index_with_photo_id(photo_id: str, embedding: list[float]):
    """Store vector in Pinecone using PostgreSQL photo ID as vector identifier."""
    index = pc.Index(PHOTOS_INDEX_NAME)
    index.upsert(
        vectors=[
            {
                "id": photo_id,
                "values": embedding,
                "metadata": {
                    "photo_id": photo_id,
                },
            },
        ],
        namespace=PHOTOS_NAMESPACE,
    )


def gen_caption_embedding(path: str) -> Optional[list[float]]:
    # At the moment, we're just using the location as the caption
    location = get_image_location(path)
    if not location:
        return None
    return gen_text_embedding(location)


def search_photos(query: str, threshold: float = 0.1) -> List[Photo]:
    """Search for photos using text query and return complete Photo objects from PostgreSQL"""
    try:
        # Generate embedding for search query
        query_embedding = gen_text_embedding(query)

        # Search pinecone index
        index = pc.Index(PHOTOS_INDEX_NAME)
        search_results = index.query(
            vector=query_embedding, top_k=5, namespace=PHOTOS_NAMESPACE
        )

        # Extract photo IDs from Pinecone results
        photo_ids = []
        for match in search_results.matches:
            if match.score < threshold:
                continue

            # The vector ID should be the PostgreSQL photo ID (string)
            try:
                photo_id = int(match.id)  # Convert string ID back to integer
                photo_ids.append(photo_id)
            except ValueError:
                # Log warning for invalid photo ID format
                logger.warning(f"Invalid photo ID format in Pinecone: {match.id}")
                continue

        if not photo_ids:
            return []

        # Fetch Photo objects from PostgreSQL using the extracted IDs
        photos = Photo.query.filter(Photo.id.in_(photo_ids)).all()
        return photos

        
    except Exception as e:
        logger.error(f"Error searching photos: {str(e)}")
        raise Exception(f"Error searching photos: {str(e)}")


def get_vector_count_in_namespace():
    """Get the count of vectors in the PHOTOS_NAMESPACE in Pinecone index."""
    try:
        index = pc.Index(PHOTOS_INDEX_NAME)
        
        # Get current vector count
        index_stats = index.describe_index_stats()
        vector_count = 0
        if hasattr(index_stats, 'namespaces') and PHOTOS_NAMESPACE in index_stats.namespaces:
            vector_count = index_stats.namespaces[PHOTOS_NAMESPACE].vector_count
        
        logger.info(f"Found {vector_count} vectors in namespace '{PHOTOS_NAMESPACE}'")
        return True, vector_count
        
    except Exception as e:
        logger.warning(f"Could not get vector count: {str(e)}")
        return False, str(e)


def delete_all_vectors_from_namespace():
    """Delete all vectors from the PHOTOS_NAMESPACE in Pinecone index."""
    try:
        index = pc.Index(PHOTOS_INDEX_NAME)
        
        # Delete all vectors in the namespace
        index.delete(delete_all=True, namespace=PHOTOS_NAMESPACE)
        logger.info(f"Successfully deleted all vectors from namespace '{PHOTOS_NAMESPACE}'")
        
        return True, "Success"
        
    except Exception as e:
        logger.error(f"Error deleting vectors from Pinecone: {str(e)}")
        return False, str(e) 