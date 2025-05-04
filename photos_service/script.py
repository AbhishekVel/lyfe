"""
Script lets you upload photos, embeds them, and stores into a vector db (pinecone).
"""

from PIL import Image as PILImage
from io import BytesIO
import os
from pathlib import Path
from typing import List
import argparse
import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel
from pinecone import Pinecone


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
    image = Image(image_bytes=get_resized_image_bytes(path))
    embeddings = model.get_embeddings(
        image=image,
        dimension=512,
    )
    return embeddings.image_embedding


def gen_search_query_embedding(query: str) -> list[float]:
    embeddings = model.get_embeddings(
        contextual_text=query,
        dimension=512,
    )
    return embeddings.text_embedding


def update_index(path: str, embedding):
    index = pc.Index("majestic-eucalyptus")
    index.upsert(
        vectors=[
            {
                "id": path,
                "values": embedding,
            },
        ],
        namespace="abhivel-photos",
    )


def upload_photos(dir: str):
    for path in find_photos_in_dir(dir):
        embedding = gen_image_embedding(path)
        update_index(path=path, embedding=embedding)


def find_photos(query: str):
    # Generate embedding for search query
    query_embedding = gen_search_query_embedding(query)

    # Search pinecone index
    index = pc.Index("majestic-eucalyptus")
    search_results = index.query(
        vector=query_embedding, top_k=3, namespace="abhivel-photos"
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

    if args.upload:
        upload_photos(args.upload_photos)
    elif args.find:
        print(find_photos(args.find))


if __name__ == "__main__":
    main()
