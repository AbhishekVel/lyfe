"""
Script lets you upload photos, embeds them, and stores into a vector db (pinecone).
"""
from main import create_app
import base64
from datetime import datetime
from models import Photo
from geopy.geocoders import Nominatim

from PIL.ExifTags import GPSTAGS
from PIL.ExifTags import TAGS
from PIL import Image as PILImage
from io import BytesIO
import os
from pathlib import Path
from typing import List, Optional
import argparse
from tqdm import tqdm
import vertexai
from vertexai.vision_models import Image as VertexImage, MultiModalEmbeddingModel
from pinecone import Pinecone
from constants import LOCATION_NAMESPACE, PHOTOS_INDEX_NAME, PHOTOS_NAMESPACE, VECTOR_DIMENSION


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
    """Resize image to 512x512 regardless of aspect ratio and return as bytes."""
    with PILImage.open(path) as img:
        # Resize to fixed 512x512 size
        resized_img = img.resize((512, 512), PILImage.Resampling.LANCZOS)

        # Convert to bytes
        img_byte_arr = BytesIO()
        resized_img.save(img_byte_arr, format=img.format)
        return img_byte_arr.getvalue()


def gen_image_embedding(image: bytes):
    image = VertexImage(image_bytes=image)
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
    geolocator = Nominatim(user_agent="abhi-agent")
    location = geolocator.reverse(f"{gps_coords[0]}, {gps_coords[1]}")
    if not location:
        return None
    return location.address

def get_image_timestamp(path: str) -> Optional[datetime]:
    """Extract timestamp from image EXIF data"""
    try:
        with PILImage.open(path) as img:
            # Get EXIF data
            exif = img._getexif()
            if not exif:
                return None
                
            # Look for DateTimeOriginal or DateTime tags
            for tag_id in exif:
                tag = TAGS.get(tag_id, tag_id)
                if tag in ["DateTimeOriginal", "DateTime"]:
                    # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                    date_str = exif[tag_id]
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    
            return None
    except:
        return None


def gen_text_embedding(text: str) -> list[float]:
    embeddings = model.get_embeddings(
        contextual_text=text,
        dimension=VECTOR_DIMENSION,
    )
    return embeddings.text_embedding

def exists_in_index(id: int, type: str) -> bool:
    index = pc.Index(PHOTOS_INDEX_NAME)
    return bool(index.fetch(
        ids=[f"{type}:{id}"], namespace=PHOTOS_NAMESPACE
    ).vectors)


def update_index(id: int, embedding: list[float], namespace: str):
    index = pc.Index(PHOTOS_INDEX_NAME)
    index.upsert(
        vectors=[
            {
                "id": str(id),
                "values": embedding,
                "metadata": {
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

def upload_photos(dir: str):
    for path in tqdm(find_photos_in_dir(dir), desc="Processing photos"):
        try:
            # First check to see if the image  is already in the database
            photo = Photo.query.filter_by(path=path).first()
            if photo:
                print(f"Photo {path} already exists in the database")
                continue
        

            # Convert resized bytes to base64
            image_bytes = get_resized_image_bytes(path)
            photo_data = base64.b64encode(image_bytes).decode('utf-8')
            file_type = path.split('.')[-1].lower()


            # Resize image and get location
            location = get_image_location(path)
            timestamp = get_image_timestamp(path)
            photo_row = Photo.create_photo(
                data=photo_data,
                file_type=file_type,
                path=path,
                location=location,
                timestamp=timestamp
            )

            image_embedding = gen_image_embedding(image_bytes)
            update_index(id=photo_row.id, embedding=image_embedding, namespace=PHOTOS_NAMESPACE)
        except Exception as e:
            print(f"Error processing photo {path}: {e}")
            continue


def find_photos(query: str):
    # Generate embedding for search query
    query_embedding = gen_text_embedding(query)

    # Search pinecone index
    index = pc.Index(PHOTOS_INDEX_NAME)
    search_results = index.query(
        vector=query_embedding, top_k=20, namespace=PHOTOS_NAMESPACE
    )

    # Return paths of matching photos
    matches = []
    for match in search_results.matches:
        matches.append(match.id)

    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Process and store photos in vector database"
    )
    parser.add_argument(
        "--upload", type=str, help="Directory containing photos to process"
    )
    parser.add_argument("--find", type=str, help="Search query to find matching photos")

    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        try:
            if args.upload:
                upload_photos(args.upload)
            elif args.find:
                print(find_photos(args.find))
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
