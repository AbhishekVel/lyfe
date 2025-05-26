# Lyfe Photo Gallery

A full-stack photo gallery application with a Python Flask backend and React TypeScript frontend. Upload, view, and search your photos with AI-powered semantic search.

## Features

### Backend (Python Flask)
- 📸 Photo storage with metadata (location, timestamp)
- 🔍 AI-powered semantic search using vector embeddings
- 💾 SQLite database with SQLAlchemy ORM
- 🔄 Batch photo upload from directories
- 📊 RESTful API with proper error handling
- 🏥 Health check endpoints

### Frontend (React TypeScript)
- 🎨 Modern, responsive photo gallery interface
- 📤 Drag & drop photo uploads with previews
- 🔍 Real-time search functionality
- 📱 Mobile-friendly responsive design
- ⚡ Lazy loading and pagination
- 🖼️ Full-screen photo viewer with modal

## Tech Stack

**Backend:**
- Python 3.9+
- Flask with SQLAlchemy
- OpenAI/Sentence Transformers for embeddings
- SQLite database
- Base64 image storage

**Frontend:**
- React 18 with TypeScript
- Axios for API communication
- React Dropzone for file uploads
- Modern CSS with Grid/Flexbox
- Responsive design

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### 1. Start the Backend

```bash
cd backend
pip install -r requirements.txt  # or use uv install
python main.py
```

The backend will start on `http://localhost:8000`

### 2. Start the Frontend

```bash
cd frontend
npm install
npm start
```

The frontend will start on `http://localhost:3000`

### 3. Open Your Browser

Navigate to `http://localhost:3000` and start uploading and viewing photos!

## Detailed Setup

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies (using uv - recommended):
   ```bash
   uv install
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   python init_db.py
   ```

4. Start the server:
   ```bash
   python main.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## API Endpoints

- `GET /health` - Health check
- `GET /photos?limit=50&offset=0` - Get photos with pagination
- `POST /upload_photos` - Upload photos (batch)
- `POST /search` - Search photos by text query
- `POST /upload` - Upload photos from directory (admin)

## Usage

### Uploading Photos
1. Click the "Upload" tab
2. Drag & drop photos or click to select
3. Add location information for each photo
4. Click "Upload Photos"

### Viewing Photos
1. Browse the gallery on the main page
2. Click any photo to view full size
3. Use pagination to navigate through collections

### Searching Photos
1. Use the search bar to find photos
2. Search by location, description, or visual content
3. Results will replace the gallery view
4. Click "View All Photos" to return to full gallery

## Project Structure

```
lyfe/
├── backend/              # Python Flask API
│   ├── main.py          # Entry point
│   ├── routes.py        # API routes
│   ├── models.py        # Database models
│   ├── photo_service.py # Photo processing
│   └── database.py      # Database setup
├── frontend/            # React TypeScript app
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── api.ts      # API service
│   │   └── App.tsx     # Main app
│   └── public/         # Static assets
└── README.md           # This file
```

## Development

### Backend Development
- Use `python main.py` for development
- Database changes require running `python init_db.py`
- Check `backend/README.md` for detailed backend setup

### Frontend Development
- Use `npm start` for hot reloading
- Build with `npm run build`
- Check `frontend/README.md` for detailed frontend setup

### Environment Variables

Backend environment variables (optional):
- `OPENAI_API_KEY` - For enhanced search capabilities
- `DATABASE_URL` - Custom database location

## Troubleshooting

### Backend Issues
- Ensure Python 3.9+ is installed
- Check if all dependencies are installed
- Verify the database is initialized

### Frontend Issues
- Ensure Node.js 16+ is installed
- Clear node_modules and reinstall if needed
- Check if backend is running on port 8000

### Connection Issues
- Backend must be running on port 8000
- Frontend assumes backend at `http://localhost:8000`
- Check firewall settings if connection fails

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both frontend and backend
5. Submit a pull request

## License

This project is part of the Lyfe application suite.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review backend and frontend README files
3. Check the API documentation
4. Create an issue in the repository 