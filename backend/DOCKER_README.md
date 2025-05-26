# Docker Setup for Photos Backend

This document explains how to build and run the photos backend application using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier management)
- Google Cloud SDK installed and authenticated (`gcloud auth application-default login`)
- Required environment variables (see Environment Variables section)

## Google Cloud Authentication

Before running the container, make sure you're authenticated with Google Cloud:

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Verify your authentication
gcloud auth application-default print-access-token
```

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# Google Cloud Platform Project ID
GCP_PROJECT_ID=your-gcp-project-id

# Pinecone API Key
PINECONE_API_KEY=your-pinecone-api-key

# Optional: Flask environment (development/production)
FLASK_ENV=production
```

## Building and Running

### Option 1: Using Docker Compose (Recommended)

The docker-compose.yml automatically mounts your Google Cloud credentials.

1. **Build and start the application:**
   ```bash
   docker-compose up --build
   ```

2. **Run in the background:**
   ```bash
   docker-compose up -d --build
   ```

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

4. **View logs:**
   ```bash
   docker-compose logs -f backend
   ```

### Option 2: Using Docker Commands

1. **Build the Docker image:**
   ```bash
   docker build -t photos-backend .
   ```

2. **Run the container with Google Cloud credentials:**
   ```bash
   docker run -d \
     --name photos-backend \
     -p 7100:7100 \
     -e GCP_PROJECT_ID=your-gcp-project-id \
     -e PINECONE_API_KEY=your-pinecone-api-key \
     -e GOOGLE_APPLICATION_CREDENTIALS=/app/gcloud/application_default_credentials.json \
     -v ~/.config/gcloud:/app/gcloud:ro \
     photos-backend
   ```

3. **Stop the container:**
   ```bash
   docker stop photos-backend
   docker rm photos-backend
   ```

## Development

For development with live code reloading and Google Cloud credentials:

```bash
docker run -d \
  --name photos-backend-dev \
  -p 7100:7100 \
  -e GCP_PROJECT_ID=your-gcp-project-id \
  -e PINECONE_API_KEY=your-pinecone-api-key \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/gcloud/application_default_credentials.json \
  -e FLASK_ENV=development \
  -v $(pwd):/app \
  -v ~/.config/gcloud:/app/gcloud:ro \
  photos-backend
```

## Health Check

The container includes a health check that monitors the `/health` endpoint. You can check the status:

```bash
docker ps
```

The STATUS column will show "healthy" or "unhealthy".

## API Endpoints

Once running, the following endpoints are available:

- **Health Check:** `GET http://localhost:7100/health`
- **Upload Photos:** `POST http://localhost:7100/upload`
- **Search Photos:** `POST http://localhost:7100/search`

## Troubleshooting

### Common Issues

1. **Google Cloud Authentication Errors:**
   - Ensure you've run `gcloud auth application-default login`
   - Verify your credentials: `gcloud auth application-default print-access-token`
   - Check that your GCP_PROJECT_ID is correct

2. **Permission Denied:**
   - Ensure Docker has permission to access the directory
   - Check if ports are already in use
   - Verify Google Cloud credentials file permissions

3. **Environment Variables Not Set:**
   - Verify your `.env` file exists and has correct values
   - For docker-compose, ensure the `.env` file is in the same directory as `docker-compose.yml`

4. **Build Failures:**
   - Clear Docker cache: `docker system prune -a`
   - Rebuild without cache: `docker-compose build --no-cache`

### Debugging

1. **Check container logs:**
   ```bash
   docker logs photos-backend
   ```

2. **Access container shell:**
   ```bash
   docker exec -it photos-backend /bin/bash
   ```

3. **Test Google Cloud authentication inside container:**
   ```bash
   docker exec -it photos-backend cat /app/gcloud/application_default_credentials.json
   ```

4. **Inspect running processes:**
   ```bash
   docker exec photos-backend ps aux
   ```

## Production Deployment

For production deployment:

1. Use a proper reverse proxy (nginx, traefik)
2. Set up proper logging and monitoring
3. Use Google Cloud service account keys instead of user credentials
4. Consider using a multi-stage build for smaller image size
5. Set resource limits in docker-compose.yml

### Production Authentication

Instead of mounting user credentials, use a service account:

1. **Create a service account:**
   ```bash
   gcloud iam service-accounts create photos-backend-service
   ```

2. **Grant necessary permissions:**
   ```bash
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:photos-backend-service@your-project-id.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

3. **Create and download key:**
   ```bash
   gcloud iam service-accounts keys create service-account-key.json \
     --iam-account=photos-backend-service@your-project-id.iam.gserviceaccount.com
   ```

4. **Mount the service account key:**
   ```bash
   docker run -d \
     -v /path/to/service-account-key.json:/app/gcloud/credentials.json:ro \
     -e GOOGLE_APPLICATION_CREDENTIALS=/app/gcloud/credentials.json \
     photos-backend
   ```

Example production docker-compose.yml additions:

```yaml
services:
  backend:
    # ... existing configuration
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
``` 