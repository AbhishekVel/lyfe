import React, { useState, useEffect, useCallback } from 'react';
import { getPhotos, Photo } from '../api';
import './PhotoGallery.css';

interface PhotoGalleryProps {
  searchResults?: Photo[];
  isSearchMode?: boolean;
}

const PhotoGallery: React.FC<PhotoGalleryProps> = ({ searchResults, isSearchMode = false }) => {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPhotos, setTotalPhotos] = useState(0);
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);
  
  const PHOTOS_PER_PAGE = 20;

  const loadPhotos = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getPhotos(PHOTOS_PER_PAGE, currentPage * PHOTOS_PER_PAGE);
      setPhotos(response.photos);
      setTotalPhotos(response.pagination.total);
    } catch (err) {
      setError('Failed to load photos. Make sure the backend is running on port 8000.');
      console.error('Error loading photos:', err);
    } finally {
      setLoading(false);
    }
  }, [currentPage, PHOTOS_PER_PAGE]);

  useEffect(() => {
    if (isSearchMode && searchResults) {
      setPhotos(searchResults);
      setLoading(false);
      return;
    }

    loadPhotos();
  }, [currentPage, isSearchMode, searchResults, loadPhotos]);

  const totalPages = Math.ceil(totalPhotos / PHOTOS_PER_PAGE);

  const handlePrevPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  const getImageSrc = (photo: Photo) => {
    return `data:image/${photo.file_type};base64,${photo.data}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="photo-gallery-loading">
        <div className="loading-spinner"></div>
        <p>Loading photos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="photo-gallery-error">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={loadPhotos} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  if (photos.length === 0) {
    return (
      <div className="photo-gallery-empty">
        <h3>No photos found</h3>
        <p>{isSearchMode ? 'Try a different search term.' : 'Upload some photos to get started!'}</p>
      </div>
    );
  }

  return (
    <div className="photo-gallery">
      {isSearchMode && (
        <div className="search-results-header">
          <h3>Search Results ({photos.length} photos)</h3>
        </div>
      )}
      
      <div className="photo-grid">
        {photos.map((photo) => (
          <div key={photo.id} className="photo-item" onClick={() => setSelectedPhoto(photo)}>
            <div className="photo-container">
              <img
                src={getImageSrc(photo)}
                alt={`Taken at ${photo.location}`}
                className="photo-thumbnail"
                loading="lazy"
              />
              <div className="photo-overlay">
                <div className="photo-info">
                  <p className="photo-location">{photo.location}</p>
                  <p className="photo-date">{formatDate(photo.created_at)}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {!isSearchMode && totalPages > 1 && (
        <div className="pagination">
          <button 
            onClick={handlePrevPage} 
            disabled={currentPage === 0}
            className="pagination-button"
          >
            Previous
          </button>
          <span className="pagination-info">
            Page {currentPage + 1} of {totalPages} ({totalPhotos} total photos)
          </span>
          <button 
            onClick={handleNextPage} 
            disabled={currentPage >= totalPages - 1}
            className="pagination-button"
          >
            Next
          </button>
        </div>
      )}

      {selectedPhoto && (
        <div className="photo-modal" onClick={() => setSelectedPhoto(null)}>
          <div className="photo-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedPhoto(null)}>
              ×
            </button>
            <img
              src={getImageSrc(selectedPhoto)}
              alt={`Full size view of ${selectedPhoto.location}`}
              className="modal-image"
            />
            <div className="modal-info">
              <h3>{selectedPhoto.location}</h3>
              <p>Taken: {formatDate(selectedPhoto.created_at)}</p>
              <p>Type: {selectedPhoto.file_type.toUpperCase()}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PhotoGallery; 