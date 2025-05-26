import React, { useState } from 'react';
import { deleteAllDataPreview, deleteAllDataConfirm, DeleteAllDataResponse } from '../api';
import './DeleteAllData.css';

interface DeleteAllDataProps {
  onDataDeleted?: () => void;
}

const DeleteAllData: React.FC<DeleteAllDataProps> = ({ onDataDeleted }) => {
  const [showDialog, setShowDialog] = useState(false);
  const [previewData, setPreviewData] = useState<DeleteAllDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteResult, setDeleteResult] = useState<DeleteAllDataResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDeleteClick = async () => {
    setLoading(true);
    setError(null);
    setDeleteResult(null);
    
    try {
      const preview = await deleteAllDataPreview();
      setPreviewData(preview);
      setShowDialog(true);
    } catch (err) {
      setError('Failed to get data preview. Make sure the backend is running.');
      console.error('Delete preview error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDelete = async () => {
    setDeleting(true);
    setError(null);
    
    try {
      const result = await deleteAllDataConfirm();
      setDeleteResult(result);
      
      if (result.success && onDataDeleted) {
        // Call the callback after a short delay to show the result
        setTimeout(() => {
          onDataDeleted();
        }, 2000);
      }
    } catch (err) {
      setError('Failed to delete data. Please try again.');
      console.error('Delete confirmation error:', err);
    } finally {
      setDeleting(false);
    }
  };

  const handleCancel = () => {
    setShowDialog(false);
    setPreviewData(null);
    setDeleteResult(null);
    setError(null);
  };

  const renderPreviewDialog = () => {
    if (!previewData || deleteResult) return null;

    return (
      <div className="delete-dialog-overlay">
        <div className="delete-dialog">
          <div className="delete-dialog-header">
            <h3>⚠️ Delete All Data</h3>
            <button className="close-button" onClick={handleCancel}>×</button>
          </div>
          
          <div className="delete-dialog-content">
            <p className="warning-text">
              This will permanently delete <strong>ALL</strong> your photos and data. This action cannot be undone.
            </p>
            
            <div className="data-summary">
              <h4>Data to be deleted:</h4>
              <ul>
                <li>
                  <strong>{previewData.data_to_delete?.postgresql_photos || 0}</strong> photos from database
                </li>
                <li>
                  <strong>{previewData.data_to_delete?.pinecone_vectors || 0}</strong> vectors from search index
                </li>
              </ul>
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">❌</span>
                {error}
              </div>
            )}
          </div>
          
          <div className="delete-dialog-actions">
            <button 
              className="cancel-button" 
              onClick={handleCancel}
              disabled={deleting}
            >
              Cancel
            </button>
            <button 
              className="confirm-delete-button" 
              onClick={handleConfirmDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Yes, Delete Everything'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderResultDialog = () => {
    if (!deleteResult) return null;

    return (
      <div className="delete-dialog-overlay">
        <div className="delete-dialog">
          <div className="delete-dialog-header">
            <h3>{deleteResult.success ? '✅ Deletion Complete' : '⚠️ Deletion Results'}</h3>
            <button className="close-button" onClick={handleCancel}>×</button>
          </div>
          
          <div className="delete-dialog-content">
            <p className={`result-message ${deleteResult.success ? 'success' : 'warning'}`}>
              {deleteResult.message}
            </p>
            
            {deleteResult.results && (
              <div className="deletion-details">
                <h4>Details:</h4>
                <div className="result-item">
                  <strong>PostgreSQL Database:</strong>
                  {deleteResult.results.postgresql.success ? (
                    <span className="success-text">
                      ✅ Deleted {deleteResult.results.postgresql.deleted} photos
                    </span>
                  ) : (
                    <span className="error-text">
                      ❌ Failed: {deleteResult.results.postgresql.error}
                    </span>
                  )}
                </div>
                <div className="result-item">
                  <strong>Pinecone Search Index:</strong>
                  {deleteResult.results.pinecone.success ? (
                    <span className="success-text">
                      ✅ Successfully cleared all vectors
                    </span>
                  ) : (
                    <span className="error-text">
                      ❌ Failed: {deleteResult.results.pinecone.error}
                    </span>
                  )}
                </div>
                
                {deleteResult.verification && (
                  <div className="verification">
                    <p>
                      <strong>Verification:</strong> {deleteResult.verification.postgresql_photos_remaining} photos remaining
                    </p>
                  </div>
                )}
              </div>
            )}

            {deleteResult.error && (
              <div className="error-message">
                <span className="error-icon">❌</span>
                {deleteResult.error}
              </div>
            )}
          </div>
          
          <div className="delete-dialog-actions">
            <button className="close-button-primary" onClick={handleCancel}>
              Close
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      <button 
        className="delete-all-button" 
        onClick={handleDeleteClick}
        disabled={loading}
        title="Delete all photos and data"
      >
        {loading ? 'Loading...' : '🗑️ Delete All Data'}
      </button>
      
      {showDialog && (deleteResult ? renderResultDialog() : renderPreviewDialog())}
    </>
  );
};

export default DeleteAllData; 