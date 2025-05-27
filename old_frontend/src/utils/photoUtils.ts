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

interface PhotoMetadata {
  location: string | null;
  coordinates: GPSCoordinates | null;
  dateTaken: Date | null;
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
 * Extract the date when the photo was taken from EXIF data
 */
export const getDateTakenFromImage = async (file: File): Promise<Date | null> => {
  try {
    // Extract EXIF data from the image file
    const exifData = await exifr.parse(file);
    
    if (!exifData) {
      return null;
    }

    // Try different EXIF date fields in order of preference
    const dateFields = [
      'DateTimeOriginal',    // When the photo was taken (most accurate)
      'CreateDate',          // Alternative field name
      'DateTime',            // File modification date (less accurate)
      'DateTimeDigitized'    // When the photo was digitized
    ];

    for (const field of dateFields) {
      if (exifData[field]) {
        const dateValue = exifData[field];
        
        // Handle different date formats
        if (dateValue instanceof Date) {
          return dateValue;
        } else if (typeof dateValue === 'string') {
          // Parse EXIF date format: "YYYY:MM:DD HH:MM:SS"
          const parsedDate = new Date(dateValue.replace(/:/g, '-').replace(' ', 'T'));
          if (!isNaN(parsedDate.getTime())) {
            return parsedDate;
          }
        }
      }
    }

    return null;
  } catch (error) {
    console.error('Error extracting date from image:', error);
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
 * Extract comprehensive metadata from image file (location and date)
 */
export const getImageMetadata = async (file: File): Promise<PhotoMetadata> => {
  try {
    // Extract both location and date in parallel
    const [coords, dateTaken] = await Promise.all([
      getGPSCoordsFromImage(file),
      getDateTakenFromImage(file)
    ]);

    let location: string | null = null;
    if (coords) {
      location = await getLocationFromCoords(coords);
    }

    return {
      location,
      coordinates: coords,
      dateTaken
    };
  } catch (error) {
    console.error('Error extracting image metadata:', error);
    return {
      location: null,
      coordinates: null,
      dateTaken: null
    };
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

/**
 * Format date for display
 */
export const formatDateTaken = (date: Date): string => {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}; 