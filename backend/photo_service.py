import os
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