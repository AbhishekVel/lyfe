# Automatic Location Extraction

This feature automatically extracts GPS coordinates from uploaded photos and converts them to human-readable location names.

## How It Works

1. **EXIF Data Extraction**: When photos are uploaded, the app uses the `exifr` library to extract EXIF metadata from the image files.

2. **GPS Coordinate Parsing**: If GPS data is found in the EXIF metadata, it extracts the latitude and longitude coordinates.

3. **Reverse Geocoding**: The coordinates are then sent to the Nominatim API (OpenStreetMap's geocoding service) to get a human-readable address.

4. **Location Display**: The extracted location is automatically populated in the location field for each photo.

## Features

- ✅ **Automatic Extraction**: Location is extracted immediately when photos are dropped/selected
- ✅ **Loading States**: Shows a spinner while extracting location data
- ✅ **Error Handling**: Displays helpful error messages when GPS data isn't available
- ✅ **Manual Override**: Users can still edit the location field manually
- ✅ **Retry Function**: Users can retry location extraction if it fails
- ✅ **No API Keys Required**: Uses the free Nominatim API

## Supported Image Formats

The location extraction works with any image format that contains EXIF data:
- JPEG (.jpg, .jpeg)
- TIFF (.tiff, .tif)
- Some RAW formats (depending on the camera)

Note: PNG, GIF, and WebP files typically don't contain EXIF data with GPS information.

## GPS Data Requirements

For location extraction to work, the photo must have been taken with:
- A device with GPS capability (smartphone, GPS-enabled camera)
- Location services enabled when the photo was taken
- The GPS data must be embedded in the EXIF metadata

## Privacy Note

- Location extraction happens entirely in the browser
- GPS coordinates are only sent to the Nominatim API for reverse geocoding
- No location data is stored or transmitted to any other services
- Users can always modify or remove location information before uploading

## Technical Implementation

### Key Files

- `src/utils/locationUtils.ts` - Core location extraction functions
- `src/components/PhotoUpload.tsx` - Integration with upload component
- `src/components/PhotoUpload.css` - Styling for location UI states

### API Used

- **Nominatim API**: `https://nominatim.openstreetmap.org/reverse`
  - Free to use with attribution
  - Rate limited (1 request per second)
  - No API key required

### Dependencies

- `exifr` - EXIF data extraction library
- Browser's native `fetch` API for geocoding requests

## Error States

The system handles various error conditions gracefully:

1. **No GPS Data**: Shows "No GPS data found" message with retry option
2. **Network Error**: Shows "Failed to extract location" with retry option
3. **API Rate Limiting**: Automatically handled with appropriate error messages
4. **Invalid Coordinates**: Fallback to "Unknown Location"

## Usage Example

1. Drag and drop a photo taken with a smartphone
2. Watch the location field automatically populate (e.g., "Main Street, San Francisco, California, United States")
3. Edit the location if needed or leave it as extracted
4. Upload the photo with the location data

## Future Enhancements

Potential improvements for future versions:
- Offline geocoding using cached data
- Support for custom geocoding services
- Batch processing optimization for multiple photos
- Location accuracy indicators
- Time zone extraction from GPS data 