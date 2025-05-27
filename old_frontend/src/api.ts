import axios from 'axios';
import { resizeImageToBase64 } from './utils/imageUtils';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Photo {
  id: number;
  data: string; // base64 encoded image data
  file_type: string;
  location: string;
  created_at: string;
  updated_at: string;
}

export interface PhotosResponse {
  success: boolean;
  photos: Photo[];
  pagination: {
    offset: number;
    limit: number;
    total: number;
    returned: number;
  };
}

export interface UploadPhotoData {
  data: string; // base64 encoded image data
  location: string;
  timestamp: string;
}

export interface UploadResponse {
  success: boolean;
  created_count: number;
  error_count: number;
  created_photos: any[];
  errors?: string[];
}

export interface SearchResult {
  photo: Photo;
  score: number;
  photo_id: number;
}

export interface SearchResponse {
  success: boolean;
  query: string;
  results: SearchResult[];
  count: number;
}

export interface DeleteAllDataResponse {
  success: boolean;
  message: string;
  data_to_delete?: {
    postgresql_photos: number;
    pinecone_vectors: number | string;
  };
  confirmation_required?: boolean;
  note?: string;
  results?: {
    postgresql: {
      before: number;
      deleted: number;
      success: boolean;
      error: string | null;
    };
    pinecone: {
      before: number | string;
      success: boolean;
      error: string | null;
    };
  };
  verification?: {
    postgresql_photos_remaining: number;
  };
  error?: string;
}

// API Functions
export const getPhotos = async (limit: number = 50, offset: number = 0): Promise<PhotosResponse> => {
  const response = await api.get(`/photos?limit=${limit}&offset=${offset}`);
  return response.data;
};

export const uploadPhotos = async (photos: UploadPhotoData[]): Promise<UploadResponse> => {
  const response = await api.post('/upload_photos', { photos });
  return response.data;
};

export const searchPhotos = async (query: string): Promise<SearchResponse> => {
  const response = await api.post('/search', { query });
  return response.data;
};

export const healthCheck = async (): Promise<{ status: string; service: string }> => {
  const response = await api.get('/health');
  return response.data;
};

export const deleteAllDataPreview = async (): Promise<DeleteAllDataResponse> => {
  const response = await api.post('/delete_all_data', {});
  return response.data;
};

export const deleteAllDataConfirm = async (): Promise<DeleteAllDataResponse> => {
  const response = await api.post('/delete_all_data', { confirmed: true });
  return response.data;
};

// Helper function to convert File to base64 with resizing
export const fileToBase64 = (file: File): Promise<string> => {
  // Use the new resize function that resizes to 512px max dimension
  return resizeImageToBase64(file, 512);
}; 