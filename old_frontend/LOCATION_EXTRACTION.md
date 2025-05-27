# Automatic Photo Metadata Extraction

This feature automatically extracts GPS coordinates and date taken from uploaded photos and converts them to human-readable location names and timestamps.

## How It Works

1. **EXIF Data Extraction**: When photos are uploaded, the app uses the `exifr` library to extract EXIF metadata from the image files.

2. **GPS Coordinate Parsing**: If GPS data is found in the EXIF metadata, it extracts the latitude and longitude coordinates.

3. **Date Extraction**: Extracts the date when the photo was taken from various EXIF date fields (DateTimeOriginal, CreateDate, DateTime, DateTimeDigitized).

4. **Reverse Geocoding**: The coordinates are then sent to the Nominatim API (OpenStreetMap's geocoding service) to get a human-readable address.

5. **Display**: The extracted location and date are automatically populated in the photo preview.

## Features

- ✅ **Automatic Extraction**: Location and date extracted immediately when photos are dropped/selected
- ✅ **Date Accuracy**: Uses DateTimeOriginal (when photo was taken) for most accurate timestamps
- ✅ **Loading States**: Shows a spinner while extracting metadata
- ✅ **Error Handling**: Displays helpful error messages when data isn't available
- ✅ **Manual Override**: Users can still edit the location field manually
- ✅ **Retry Function**: Users can retry metadata extraction if it fails
- ✅ **No API Keys Required**: Uses the free Nominatim API

## Supported Image Formats

The metadata extraction works with any image format that contains EXIF data:
- JPEG (.jpg, .jpeg) - Most common for photos with full EXIF data
- TIFF (.tiff, .tif) - Professional cameras and scanners
- Some RAW formats (depending on the camera and exifr support)

Note: PNG, GIF, and WebP files typically don't contain EXIF data with GPS or date information.

## EXIF Data Requirements

For metadata extraction to work, the photo must have been taken with:

### For Location:
- A device with GPS capability (smartphone, GPS-enabled camera)
- Location services enabled when the photo was taken
- The GPS data must be embedded in the EXIF metadata

### For Date/Time:
- Any digital camera or smartphone that records timestamp metadata
- One of the following EXIF fields must be present:
  - `DateTimeOriginal` (preferred - when photo was taken)
  - `CreateDate` (alternative field name)
  - `DateTime` (file modification date)
  - `DateTimeDigitized` (when photo was digitized)

## Privacy Note

- Metadata extraction happens entirely in the browser
- GPS coordinates are only sent to the Nominatim API for reverse geocoding
- No location or date data is stored or transmitted to any other services
- Users can always modify or remove information before uploading

## Technical Implementation

### Key Files

- `src/utils/photoUtils.ts` - Core metadata extraction functions
- `src/components/PhotoUpload.tsx` - Integration with upload component
- `src/components/PhotoUpload.css` - Styling for metadata UI states

### New Functions

- `getDateTakenFromImage()` - Extracts date from EXIF data
- `getImageMetadata()` - Combines location and date extraction
- `formatDateTaken()` - Formats dates for display

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

1. **No EXIF Data**: Shows "No EXIF data found" message with retry option
2. **No GPS Data**: Shows "No GPS data found" when location can't be extracted
3. **Network Error**: Shows "Failed to extract metadata" with retry option
4. **API Rate Limiting**: Automatically handled with appropriate error messages
5. **Invalid Coordinates/Dates**: Fallback to "Unknown Location" or current timestamp

## Usage Example

1. Drag and drop a photo taken with a smartphone
2. Watch the location field automatically populate (e.g., "Main Street, San Francisco, California, United States")
3. See the date taken displayed (e.g., "📅 Taken: December 15, 2023 at 2:30 PM")
4. Edit the location if needed or leave it as extracted
5. Upload the photo with both location and original timestamp

## Timestamp Behavior

- **If date extracted**: Uses the actual date/time when the photo was taken
- **If no date found**: Falls back to current upload time
- **Format**: ISO 8601 format (e.g., "2023-12-15T14:30:00.000Z")
- **Timezone**: Preserved from original EXIF data when available

## Future Enhancements

Potential improvements for future versions:
- Offline geocoding using cached data
- Support for custom geocoding services
- Batch processing optimization for multiple photos
- Location accuracy indicators
- Time zone detection and conversion
- Camera make/model extraction
- Additional EXIF metadata display (ISO, aperture, etc.) 