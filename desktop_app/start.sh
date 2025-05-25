#!/bin/bash

echo "🚀 Starting Photo Gallery Electron App..."
echo "📁 Looking for photos in: ~/Desktop/local_photos"

# Check if photos directory exists
if [ ! -d "~/Desktop/local_photos" ]; then
    echo "📂 Creating photos directory..."
    mkdir -p ~/Desktop/local_photos
    echo "ℹ️  Add some image files to ~/Desktop/local_photos to see them in the gallery"
fi

# Start the Electron app
npm start 