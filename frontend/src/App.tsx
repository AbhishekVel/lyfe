import React, { useState, useEffect } from 'react';
import './App.css';
import PhotoGallery from './components/PhotoGallery';
import PhotoUpload from './components/PhotoUpload';
import SearchBar from './components/SearchBar';
import { Photo, healthCheck } from './api';

type ViewMode = 'gallery' | 'upload';

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('gallery');
  const [searchResults, setSearchResults] = useState<Photo[] | undefined>(undefined);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  useEffect(() => {
    checkBackendConnection();
  }, []);

  const checkBackendConnection = async () => {
    try {
      await healthCheck();
      setBackendStatus('connected');
    } catch (error) {
      setBackendStatus('disconnected');
      console.error('Backend connection failed:', error);
    }
  };

  const handleSearchResults = (results: Photo[]) => {
    setSearchResults(results);
    setIsSearchMode(true);
    setViewMode('gallery'); // Switch to gallery view when searching
  };

  const handleClearSearch = () => {
    setSearchResults(undefined);
    setIsSearchMode(false);
  };

  const handleUploadComplete = () => {
    // Refresh the gallery after successful upload
    setRefreshTrigger(prev => prev + 1);
    // Clear search mode to show all photos including newly uploaded ones
    handleClearSearch();
  };

  const retryConnection = () => {
    setBackendStatus('checking');
    checkBackendConnection();
  };

  if (backendStatus === 'checking') {
    return (
      <div className="app">
        <div className="app-loading">
          <div className="loading-spinner"></div>
          <h2>Connecting to backend...</h2>
          <p>Checking connection to localhost:8000</p>
        </div>
      </div>
    );
  }

  if (backendStatus === 'disconnected') {
    return (
      <div className="app">
        <div className="app-error">
          <h2>Backend Disconnected</h2>
          <p>Unable to connect to the backend server at localhost:8000</p>
          <p>Please make sure the backend is running and try again.</p>
          <button onClick={retryConnection} className="retry-connection-button">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">📸 Lyfe Photo Gallery</h1>
          <nav className="app-nav">
            <button 
              className={`nav-button ${viewMode === 'gallery' ? 'active' : ''}`}
              onClick={() => setViewMode('gallery')}
            >
              Gallery
            </button>
            <button 
              className={`nav-button ${viewMode === 'upload' ? 'active' : ''}`}
              onClick={() => setViewMode('upload')}
            >
              Upload
            </button>
          </nav>
        </div>
      </header>

      <main className="app-main">
        {viewMode === 'gallery' && (
          <>
            <SearchBar 
              onSearchResults={handleSearchResults}
              onClearSearch={handleClearSearch}
              isSearchMode={isSearchMode}
            />
            <PhotoGallery 
              searchResults={searchResults}
              isSearchMode={isSearchMode}
              key={refreshTrigger} // Force re-render when photos are uploaded
            />
          </>
        )}
        
        {viewMode === 'upload' && (
          <div className="upload-container">
            <div className="upload-header">
              <h2>Upload Photos</h2>
              <p>Select or drag & drop your photos to upload them to your gallery</p>
            </div>
            <PhotoUpload onUploadComplete={handleUploadComplete} />
          </div>
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <p>
            <span className={`status-indicator ${backendStatus}`}></span>
            Connected to backend at localhost:8000
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
