import axios from 'axios';

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

export interface SearchResponse {
  success: boolean;
  query: string;
  matches: Photo[];
  count: number;
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

// Helper function to convert File to base64
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        // Remove the data URL prefix and return just the base64 data
        const base64Data = reader.result.split(',')[1];
        resolve(base64Data);
      } else {
        reject(new Error('Failed to convert file to base64'));
      }
    };
    reader.onerror = error => reject(error);
  });
}; 