import exifr from 'exifr';

interface GPSCoordinates {
  latitude: number;
  longitude: number;
}

interface NominatimResponse {
  display_name: string;
  address: {
    road?: string;
    city?: string;
    state?: string;
    country?: string;
    postcode?: string;
  };
}

/**
 * Extract GPS coordinates from image EXIF data
 */
export const getGPSCoordsFromImage = async (file: File): Promise<GPSCoordinates | null> => {
  try {
    // Extract EXIF data from the image file
    const exifData = await exifr.parse(file);
    
    if (!exifData || !exifData.latitude || !exifData.longitude) {
      return null;
    }

    return {
      latitude: exifData.latitude,
      longitude: exifData.longitude
    };
  } catch (error) {
    console.error('Error extracting GPS coordinates:', error);
    return null;
  }
};

/**
 * Get location name from GPS coordinates using Nominatim API
 */
export const getLocationFromCoords = async (coords: GPSCoordinates): Promise<string | null> => {
  try {
    const { latitude, longitude } = coords;
    
    // Use Nominatim API for reverse geocoding
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'Lyfe-Photo-Gallery/1.0'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`Nominatim API error: ${response.status}`);
    }

    const data: NominatimResponse = await response.json();
    
    if (data.display_name) {
      // Format a nice location string
      const address = data.address || {};
      const parts = [];
      
      if (address.road) parts.push(address.road);
      if (address.city) parts.push(address.city);
      if (address.state) parts.push(address.state);
      if (address.country) parts.push(address.country);
      
      return parts.length > 0 ? parts.join(', ') : data.display_name;
    }

    return null;
  } catch (error) {
    console.error('Error getting location from coordinates:', error);
    return null;
  }
};

/**
 * Extract location from image file (combines GPS extraction and geocoding)
 */
export const getImageLocation = async (file: File): Promise<string | null> => {
  try {
    const coords = await getGPSCoordsFromImage(file);
    
    if (!coords) {
      return null;
    }

    return await getLocationFromCoords(coords);
  } catch (error) {
    console.error('Error getting image location:', error);
    return null;
  }
};

/**
 * Format coordinates as a readable string
 */
export const formatCoordinates = (coords: GPSCoordinates): string => {
  const { latitude, longitude } = coords;
  const latDir = latitude >= 0 ? 'N' : 'S';
  const lonDir = longitude >= 0 ? 'E' : 'W';
  
  return `${Math.abs(latitude).toFixed(6)}°${latDir}, ${Math.abs(longitude).toFixed(6)}°${lonDir}`;
}; 