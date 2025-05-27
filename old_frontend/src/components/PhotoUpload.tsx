import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadPhotos, fileToBase64, UploadPhotoData } from '../api';
import { getImageMetadata, formatDateTaken } from '../utils/photoUtils';
import './PhotoUpload.css';

interface PhotoUploadProps {
  onUploadComplete: () => void;
}

interface PreviewPhoto {
  file: File;
  preview: string;
  location: string;
  dateTaken: Date | null;
  locationLoading: boolean;
  locationError?: string;
}

const PhotoUpload: React.FC<PhotoUploadProps> = ({ onUploadComplete }) => {
  const [previews, setPreviews] = useState<PreviewPhoto[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const extractMetadataFromImage = async (file: File, index: number) => {
    try {
      setPreviews(prev => 
        prev.map((preview, i) => 
          i === index ? { ...preview, locationLoading: true, locationError: undefined } : preview
        )
      );

      const metadata = await getImageMetadata(file);
      
      setPreviews(prev => 
        prev.map((preview, i) => 
          i === index ? { 
            ...preview, 
            location: metadata.location || 'Unknown Location',
            dateTaken: metadata.dateTaken,
            locationLoading: false,
            locationError: !metadata.location && !metadata.dateTaken ? 'No EXIF data found' : 
                          !metadata.location ? 'No GPS data found' : undefined
          } : preview
        )
      );
    } catch (error) {
      console.error('Error extracting metadata:', error);
      setPreviews(prev => 
        prev.map((preview, i) => 
          i === index ? { 
            ...preview, 
            locationLoading: false,
            locationError: 'Failed to extract metadata'
          } : preview
        )
      );
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const imageFiles = acceptedFiles.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length !== acceptedFiles.length) {
      setError('Some files were skipped. Only image files are allowed.');
    } else {
      setError(null);
    }

    const newPreviews = imageFiles.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      location: 'Unknown Location',
      dateTaken: null,
      locationLoading: false
    }));

    setPreviews(prev => {
      const allPreviews = [...prev, ...newPreviews];
      
      // Extract metadata for each new image
      newPreviews.forEach((_, newIndex) => {
        const actualIndex = prev.length + newIndex;
        extractMetadataFromImage(imageFiles[newIndex], actualIndex);
      });
      
      return allPreviews;
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp', '.bmp']
    },
    multiple: true
  });

  const removePreview = (index: number) => {
    setPreviews(prev => {
      const newPreviews = [...prev];
      URL.revokeObjectURL(newPreviews[index].preview);
      newPreviews.splice(index, 1);
      return newPreviews;
    });
  };

  const updateLocation = (index: number, location: string) => {
    setPreviews(prev => 
      prev.map((preview, i) => 
        i === index ? { ...preview, location } : preview
      )
    );
  };

  const retryMetadataExtraction = (index: number) => {
    const preview = previews[index];
    if (preview) {
      extractMetadataFromImage(preview.file, index);
    }
  };

  const handleUpload = async () => {
    if (previews.length === 0) {
      setError('Please select at least one photo to upload.');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);
    setUploadProgress('Preparing photos...');

    try {
      const uploadData: UploadPhotoData[] = [];

      for (let i = 0; i < previews.length; i++) {
        const preview = previews[i];
        setUploadProgress(`Resizing and processing photo ${i + 1} of ${previews.length}...`);
        
        const base64Data = await fileToBase64(preview.file);
        
        // Use extracted date if available, otherwise use current time
        const timestamp = preview.dateTaken ? preview.dateTaken.toISOString() : new Date().toISOString();
        
        uploadData.push({
          data: base64Data,
          location: preview.location || 'Unknown Location',
          timestamp: timestamp
        });
      }

      setUploadProgress('Uploading to server...');
      const response = await uploadPhotos(uploadData);

      if (response.success) {
        setSuccess(`Successfully uploaded ${response.created_count} photo${response.created_count !== 1 ? 's' : ''}!`);
        setPreviews([]);
        onUploadComplete();
        
        if (response.error_count > 0) {
          setError(`${response.error_count} photo${response.error_count !== 1 ? 's' : ''} failed to upload. Check console for details.`);
          console.error('Upload errors:', response.errors);
        }
      } else {
        setError('Upload failed. Please try again.');
        if (response.errors) {
          console.error('Upload errors:', response.errors);
        }
      }
    } catch (err) {
      setError('Upload failed. Make sure the backend is running on port 8000.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
      setUploadProgress('');
    }
  };

  const clearAll = () => {
    previews.forEach(preview => URL.revokeObjectURL(preview.preview));
    setPreviews([]);
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="photo-upload">
      <div className="upload-section">
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'disabled' : ''}`}
        >
          <input {...getInputProps()} disabled={uploading} />
          <div className="dropzone-content">
            <div className="upload-icon">📷</div>
            {isDragActive ? (
              <p>Drop the photos here...</p>
            ) : (
              <>
                <p>Drag & drop photos here, or <span className="click-text">click to select</span></p>
                <p className="upload-hint">Supports JPEG, PNG, GIF, WebP, and BMP files</p>
                <p className="upload-hint">📍 Location and 📅 date will be automatically extracted from EXIF data</p>
                <p className="upload-hint">🖼️ Images will be resized to 512px (max dimension) for optimal processing</p>
              </>
            )}
          </div>
        </div>

        {error && (
          <div className="upload-message error">
            <span className="message-icon">❌</span>
            {error}
          </div>
        )}

        {success && (
          <div className="upload-message success">
            <span className="message-icon">✅</span>
            {success}
          </div>
        )}

        {uploading && (
          <div className="upload-progress">
            <div className="progress-spinner"></div>
            <span>{uploadProgress}</span>
          </div>
        )}
      </div>

      {previews.length > 0 && (
        <div className="preview-section">
          <div className="preview-header">
            <h3>Photos to Upload ({previews.length})</h3>
            <div className="preview-actions">
              <button 
                onClick={clearAll} 
                className="clear-button"
                disabled={uploading}
              >
                Clear All
              </button>
              <button 
                onClick={handleUpload} 
                className="upload-button"
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Upload Photos'}
              </button>
            </div>
          </div>

          <div className="preview-grid">
            {previews.map((preview, index) => (
              <div key={index} className="preview-item">
                <div className="preview-image-container">
                  <img 
                    src={preview.preview} 
                    alt="Preview" 
                    className="preview-image"
                  />
                  <button
                    onClick={() => removePreview(index)}
                    className="remove-button"
                    disabled={uploading}
                  >
                    ×
                  </button>
                </div>
                <div className="preview-details">
                  <div className="location-input-container">
                    <input
                      type="text"
                      value={preview.location}
                      onChange={(e) => updateLocation(index, e.target.value)}
                      placeholder="Enter location..."
                      className="location-input"
                      disabled={uploading || preview.locationLoading}
                    />
                    {preview.locationLoading && (
                      <div className="location-status loading">
                        <div className="location-spinner"></div>
                        <span>Extracting metadata...</span>
                      </div>
                    )}
                    {preview.locationError && (
                      <div className="location-status error">
                        <span>⚠️ {preview.locationError}</span>
                        <button
                          onClick={() => retryMetadataExtraction(index)}
                          className="retry-location-button"
                          disabled={uploading || preview.locationLoading}
                        >
                          Retry
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="file-info">
                    <span className="file-name">{preview.file.name}</span>
                    <span className="file-size">
                      {(preview.file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                    {preview.dateTaken && (
                      <span className="date-taken">
                        📅 Taken: {formatDateTaken(preview.dateTaken)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PhotoUpload; 