# Lyfe Photo Gallery Frontend

A modern, responsive React application for viewing and uploading photos. This frontend connects to a local backend API running on port 8000.

## Features

- 📸 **Photo Gallery**: Browse photos in a responsive grid layout with pagination
- 🔍 **Search**: Search photos by description, location, or content using semantic search
- 📤 **Upload**: Drag & drop or select multiple photos for upload
- 🎨 **Modern UI**: Beautiful, responsive design with hover effects and animations
- 📱 **Mobile Friendly**: Optimized for mobile devices
- 🔄 **Real-time Updates**: Automatically refreshes gallery after uploads
- ⚡ **Fast**: Lazy loading images and optimized performance

## Technologies Used

- **React 18** with TypeScript
- **Axios** for API communication
- **React Dropzone** for file uploads
- **CSS3** with modern features (Grid, Flexbox, CSS Variables)
- **Responsive Design** with mobile-first approach

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Backend API running on `http://localhost:8000`

## Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## API Endpoints

The frontend connects to the following backend endpoints:

- `GET /health` - Health check
- `GET /photos` - Get photos with pagination
- `POST /upload_photos` - Upload photos (batch)
- `POST /search` - Search photos

## Usage

### Viewing Photos
- Navigate to the Gallery tab to view all photos
- Click on any photo to view it in full size
- Use pagination controls to browse through pages

### Searching Photos
- Use the search bar to find photos by description or location
- Search results will replace the gallery view
- Click "View All Photos" to return to the full gallery

### Uploading Photos
- Navigate to the Upload tab
- Drag & drop photos or click to select files
- Add location information for each photo
- Click "Upload Photos" to upload to the backend

## Project Structure

```
src/
├── components/           # React components
│   ├── PhotoGallery.tsx  # Main gallery component
│   ├── PhotoUpload.tsx   # Upload interface
│   ├── SearchBar.tsx     # Search functionality
│   └── *.css             # Component styles
├── api.ts               # API service layer
├── App.tsx              # Main application
├── App.css              # Global app styles
└── index.tsx            # Application entry point
```

## Features in Detail

### Photo Gallery
- Responsive grid layout
- Hover effects with photo information
- Full-screen modal view
- Pagination for large collections
- Error handling and loading states

### Photo Upload
- Drag & drop interface
- Multiple file selection
- Photo previews before upload
- Location tagging
- Progress indicators
- File type validation

### Search
- Real-time search functionality
- Search by location or content
- Results highlighting
- Clear search option

## Development

### Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

### Customization

You can customize the API base URL by modifying the `API_BASE_URL` constant in `src/api.ts`.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Lyfe application suite.
