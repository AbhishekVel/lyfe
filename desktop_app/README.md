# 📸 Photo Gallery Electron App

A beautiful desktop application built with Electron that displays photo thumbnails from your local directory.

## Features

- 🖼️ Displays photos as thumbnails in a responsive grid layout
- 🔍 Search photos by filename
- 📏 Adjustable thumbnail sizes (100px - 300px)
- 🖱️ Click photos to view them full-size in a modal
- 🔄 Refresh button to reload photos
- 📱 Responsive design that works on different screen sizes
- ⌨️ Keyboard shortcuts (ESC to close modal, F5/Cmd+R to refresh)

## Prerequisites

- Node.js (version 14 or higher)
- npm (comes with Node.js)

## Setup & Installation

1. **Navigate to the application directory:**
   ```bash
   cd desktop_app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create the photos directory (if it doesn't exist):**
   ```bash
   mkdir -p ~/Desktop/local_photos
   ```

4. **Add some photos to the directory:**
   - Copy some image files (jpg, png, gif, bmp, webp, tiff) to `~/Desktop/local_photos`
   - The app will automatically detect and display these images

## Running the Application

**Start the application:**
```bash
npm start
```

**For development (with auto-reload):**
```bash
npm run dev
```

## Usage

1. **Launch the app** using `npm start`
2. **Browse photos** - All images from `~/Desktop/local_photos` will be displayed as thumbnails
3. **Search** - Use the search bar to filter photos by filename
4. **Resize thumbnails** - Use the slider to adjust thumbnail size
5. **View full-size** - Click any photo to view it in full resolution
6. **Refresh** - Click the refresh button or press F5/Cmd+R to reload photos

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)
- TIFF (.tiff)

## Keyboard Shortcuts

- `Escape` - Close photo modal
- `F5` or `Cmd+R` - Refresh photo gallery

## Customization

The photo directory is currently hardcoded to `~/Desktop/local_photos`. To change this:

1. Open `src/main.js`
2. Find the line: `const photosPath = path.join(os.homedir(), 'Desktop', 'local_photos');`
3. Change the path to your desired directory

## Troubleshooting

**No photos showing up?**
- Make sure the `~/Desktop/local_photos` directory exists
- Check that you have image files in the directory
- Verify the files have supported extensions
- Try clicking the refresh button

**App won't start?**
- Make sure you've run `npm install`
- Check that you have Node.js installed (`node --version`)
- Try deleting `node_modules` and running `npm install` again

## Development

The app structure:
- `src/main.js` - Main Electron process
- `src/index.html` - UI layout
- `src/styles.css` - Styling
- `src/renderer.js` - Frontend logic
- `package.json` - Dependencies and scripts

To modify the app, edit the files in the `src/` directory and restart the application.

## License

MIT License 