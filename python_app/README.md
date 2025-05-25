# Photo Vector Database Service

A Flask web service for uploading photos to a vector database and searching them using text queries.

## Features

- Upload photos from a directory to Pinecone vector database
- Generate embeddings using Google Vertex AI's multimodal embedding model
- Extract GPS location data from photo EXIF and create location-based embeddings
- Search photos using natural language text queries

## Setup

1. Install dependencies using uv:
```bash
uv sync
```

2. Set up environment variables:
```bash
export GCP_PROJECT_ID="your-gcp-project-id"
export PINECONE_API_KEY="your-pinecone-api-key"
```

3. Make sure you have the `constants.py` file with the required constants:
   - `LOCATION_NAMESPACE`
   - `PHOTOS_INDEX_NAME`
   - `PHOTOS_NAMESPACE`
   - `VECTOR_DIMENSION`

## Running the Service

```bash
uv run python app.py
```

The service will start on `http://localhost:7100`

## API Endpoints

### Health Check
- **GET** `/health`
- Returns service status

### Upload Photos
- **POST** `/upload`
- Upload photos from a directory to the vector database
- **Request Body:**
```json
{
  "directory": "/path/to/photos"
}
```
- **Response:**
```json
{
  "success": true,
  "message": "Processed 5 out of 5 photos",
  "details": {
    "processed": 5,
    "total_found": 5,
    "errors": []
  }
}
```

### Search Photos
- **POST** `/search`
- Search for photos using a text query
- **Request Body:**
```json
{
  "query": "beach sunset"
}
```
- **Response:**
```json
{
  "success": true,
  "query": "beach sunset",
  "matches": [
    {
      "path": "/path/to/photo1.png",
      "score": 0.85,
      "metadata": {
        "path": "/path/to/photo1.png"
      }
    }
  ],
  "count": 1
}
```

## Notes

- Only PNG files are currently supported
- Photos are resized to 512px width while maintaining aspect ratio
- GPS coordinates are extracted from EXIF data when available
- Both image embeddings and location-based text embeddings are stored
- Duplicate processing is avoided by checking if files are already in the index
