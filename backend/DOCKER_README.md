# Docker Setup for Photos Backend

This document explains how to build and run the photos backend application using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier management)
- Google Cloud SDK installed and authenticated (`gcloud auth application-default login`)
- Required environment variables (see Environment Variables section)

## Services

This Docker setup includes two main services:

### 1. Backend Service
- **Image**: Custom built from Dockerfile
- **Port**: 7100
- **Purpose**: Flask API for photo processing and search

### 2. PostgreSQL Database
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Purpose**: Data storage for photo metadata and application data
- **Database**: `photos_db`
- **Username**: `postgres`
- **Password**: `password123`

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

# PostgreSQL Database Configuration (optional - defaults provided)
POSTGRES_DB=photos_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password123
```

## Building and Running

### Option 1: Using Docker Compose (Recommended)

The docker-compose.yml automatically mounts your Google Cloud credentials and sets up both backend and database.

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
   docker-compose logs -f postgres
   ```

### Option 2: Using Docker Commands

1. **Build the Docker image:**
   ```bash
   docker build -t photos-backend .
   ```

2. **Run PostgreSQL container:**
   ```bash
   docker run -d \
     --name photos-postgres \
     -p 5432:5432 \
     -e POSTGRES_DB=photos_db \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=password123 \
     -v postgres_data:/var/lib/postgresql/data \
     postgres:15-alpine
   ```

3. **Run the backend container:**
   ```bash
   docker run -d \
     --name photos-backend \
     -p 7100:7100 \
     -e GCP_PROJECT_ID=your-gcp-project-id \
     -e PINECONE_API_KEY=your-pinecone-api-key \
     -e GOOGLE_APPLICATION_CREDENTIALS=/app/gcloud/application_default_credentials.json \
     -v ~/.config/gcloud:/app/gcloud:ro \
     --link photos-postgres:postgres \
     photos-backend
   ```

4. **Stop the containers:**
   ```bash
   docker stop photos-backend photos-postgres
   docker rm photos-backend photos-postgres
   ```

## Database Management

### Connecting to PostgreSQL

**From host machine:**
```bash
# Using psql (if installed locally)
psql -h localhost -p 5432 -U postgres -d photos_db

# Using Docker
docker exec -it photos-postgres psql -U postgres -d photos_db
```

**From backend container:**
```bash
# The backend can connect using hostname 'postgres'
DATABASE_URL=postgresql://postgres:password123@postgres:5432/photos_db
```

### Common Database Operations

1. **List databases:**
   ```bash
   docker exec photos-postgres psql -U postgres -c "\l"
   ```

2. **List tables in photos_db:**
   ```bash
   docker exec photos-postgres psql -U postgres -d photos_db -c "\dt"
   ```

3. **Run SQL commands:**
   ```bash
   docker exec photos-postgres psql -U postgres -d photos_db -c "SELECT version();"
   ```

4. **Import SQL file:**
   ```bash
   docker exec -i photos-postgres psql -U postgres -d photos_db < your_file.sql
   ```

5. **Create backup:**
   ```bash
   docker exec photos-postgres pg_dump -U postgres photos_db > backup.sql
   ```

6. **Restore backup:**
   ```bash
   docker exec -i photos-postgres psql -U postgres -d photos_db < backup.sql
   ```

### Database Schema

The database starts empty. You can create your own schema as needed. Here's an example for photo metadata:

```sql
-- Example schema (not created automatically)
CREATE TABLE photos (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL UNIQUE,
    file_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Add your columns as needed
);
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
  --link photos-postgres:postgres \
  photos-backend
```

## Health Check

Both containers include health checks:

```bash
# Check container status
docker ps

# Check specific service health
docker-compose ps
```

The STATUS column will show "healthy" or "unhealthy".

## API Endpoints

Once running, the following endpoints are available:

- **Health Check:** `GET http://localhost:7100/health`
- **Upload Photos:** `POST http://localhost:7100/upload`
- **Search Photos:** `POST http://localhost:7100/search`

## Data Persistence

- **PostgreSQL Data**: Stored in `postgres_data` volume
- **Photo Files**: Stored in `photo_data` volume
- **Volumes persist** even when containers are removed

### Managing Volumes

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect backend_postgres_data

# Remove volumes (⚠️ This deletes data!)
docker-compose down -v
```

## Troubleshooting

### Common Issues

1. **Google Cloud Authentication Errors:**
   - Ensure you've run `gcloud auth application-default login`
   - Verify your credentials: `gcloud auth application-default print-access-token`
   - Check that your GCP_PROJECT_ID is correct

2. **Database Connection Errors:**
   - Verify PostgreSQL container is running: `docker ps`
   - Check database logs: `docker-compose logs postgres`
   - Ensure port 5432 is not used by another service
   - Test connection: `docker exec photos-postgres psql -U postgres -d photos_db -c "SELECT 1;"`

3. **Port Conflicts:**
   - Backend port 7100: `lsof -i :7100`
   - Database port 5432: `lsof -i :5432`
   - Change ports in docker-compose.yml if needed

4. **Permission Denied:**
   - Ensure Docker has permission to access directories
   - Verify Google Cloud credentials file permissions

5. **Environment Variables Not Set:**
   - Verify your `.env` file exists and has correct values
   - For docker-compose, ensure the `.env` file is in the same directory as `docker-compose.yml`

6. **Build Failures:**
   - Clear Docker cache: `docker system prune -a`
   - Rebuild without cache: `docker-compose build --no-cache`

### Debugging

1. **Check container logs:**
   ```bash
   docker-compose logs backend
   docker-compose logs postgres
   ```

2. **Access container shells:**
   ```bash
   docker exec -it photos-backend /bin/bash
   docker exec -it photos-postgres /bin/bash
   ```

3. **Test database connectivity:**
   ```bash
   # From host
   docker exec photos-postgres pg_isready -U postgres

   # From backend container
   docker exec backend-backend-1 nc -z postgres 5432
   ```

4. **Monitor resource usage:**
   ```bash
   docker stats
   ```

## Production Deployment

For production deployment:

1. Use a proper reverse proxy (nginx, traefik)
2. Set up proper logging and monitoring
3. Use Google Cloud service account keys instead of user credentials
4. Use strong database passwords and restrict access
5. Set resource limits in docker-compose.yml
6. Use Docker secrets for sensitive environment variables
7. Set up database backups
8. Consider using managed PostgreSQL (Google Cloud SQL, AWS RDS)

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

### Production Database Security

1. **Use strong passwords:**
   ```bash
   POSTGRES_PASSWORD=$(openssl rand -base64 32)
   ```

2. **Restrict network access:**
   ```yaml
   services:
     postgres:
       ports: [] # Remove port mapping for internal access only
   ```

3. **Set up regular backups:**
   ```bash
   # Add to crontab
   0 2 * * * docker exec photos-postgres pg_dump -U postgres photos_db | gzip > backup_$(date +%Y%m%d).sql.gz
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
  
  postgres:
    # ... existing configuration
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
``` 