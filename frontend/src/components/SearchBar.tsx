import React, { useState } from 'react';
import { searchPhotos, Photo } from '../api';
import './SearchBar.css';

interface SearchBarProps {
  onSearchResults: (results: Photo[]) => void;
  onClearSearch: () => void;
  isSearchMode: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearchResults, onClearSearch, isSearchMode }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await searchPhotos(query.trim());
      if (response.success) {
        // Extract photos from search results while maintaining order
        const photos = response.results.map(result => result.photo);
        onSearchResults(photos);
        if (response.count === 0) {
          setError('No photos found matching your search');
        }
      } else {
        setError('Search failed. Please try again.');
      }
    } catch (err) {
      setError('Search failed. Make sure the backend is running on port 8000.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQuery('');
    setError(null);
    onClearSearch();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    if (error) {
      setError(null);
    }
  };

  return (
    <div className="search-bar">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-container">
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Search photos by description, location, or content..."
            className={`search-input ${error ? 'error' : ''}`}
            disabled={loading}
          />
          <div className="search-buttons">
            {isSearchMode && (
              <button
                type="button"
                onClick={handleClear}
                className="clear-search-button"
                disabled={loading}
                title="Clear search"
              >
                ✕
              </button>
            )}
            <button
              type="submit"
              className="search-button"
              disabled={loading || !query.trim()}
              title="Search photos"
            >
              {loading ? (
                <div className="search-spinner"></div>
              ) : (
                '🔍'
              )}
            </button>
          </div>
        </div>
        
        {error && (
          <div className="search-error">
            {error}
          </div>
        )}
      </form>
      
      {isSearchMode && (
        <div className="search-status">
          <span className="search-mode-indicator">Search Mode Active</span>
          <button onClick={handleClear} className="view-all-button">
            View All Photos
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchBar; 