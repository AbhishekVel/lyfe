#!/bin/bash

echo "🧪 Testing Photo Gallery with Performance Optimizations"
echo "=================================================="

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Check if photos directory exists
PHOTOS_DIR="$HOME/Desktop/local_photos"
if [ ! -d "$PHOTOS_DIR" ]; then
    echo "📁 Creating photos directory: $PHOTOS_DIR"
    mkdir -p "$PHOTOS_DIR"
    echo "ℹ️  You can add some large image files to test the thumbnail generation"
fi

# Check if any photos exist
PHOTO_COUNT=$(find "$PHOTOS_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" -o -iname "*.bmp" -o -iname "*.webp" -o -iname "*.tiff" \) | wc -l)

echo "📸 Found $PHOTO_COUNT photo(s) in $PHOTOS_DIR"

if [ "$PHOTO_COUNT" -eq 0 ]; then
    echo "⚠️  No photos found! Add some image files to the directory for testing."
    echo "   You can copy images from your Downloads or Pictures folder:"
    echo "   cp ~/Downloads/*.jpg ~/Desktop/local_photos/"
    echo "   cp ~/Pictures/*.png ~/Desktop/local_photos/"
fi

echo "🚀 Starting optimized photo gallery..."
echo "✨ Features enabled:"
echo "   • Thumbnail generation and caching"
echo "   • Lazy loading (only loads visible photos)"
echo "   • Pagination (50 photos at a time)"
echo "   • Search and filtering"
echo "   • Performance optimizations for large images"

npm start 