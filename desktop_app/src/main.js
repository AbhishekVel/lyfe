const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const sharp = require('sharp');

// Enable live reload for development
if (process.argv.includes('--dev')) {
  require('electron-reload')(__dirname, {
    electron: path.join(__dirname, '..', 'node_modules', '.bin', 'electron'),
    hardResetMethod: 'exit'
  });
}

let mainWindow;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    title: 'Photo Gallery',
    icon: path.join(__dirname, 'assets', 'icon.png') // Optional: add an icon
  });

  // Load the HTML file
  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Open DevTools in development
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Create thumbnails directory if it doesn't exist
function ensureThumbnailsDir() {
  const thumbnailsDir = path.join(os.tmpdir(), 'photo-gallery-thumbnails');
  if (!fs.existsSync(thumbnailsDir)) {
    fs.mkdirSync(thumbnailsDir, { recursive: true });
  }
  return thumbnailsDir;
}

// Generate thumbnail for an image
async function generateThumbnail(imagePath, thumbnailPath, size = 300) {
  try {
    await sharp(imagePath)
      .resize(size, size, {
        fit: 'cover',
        position: 'center'
      })
      .jpeg({ quality: 85 })
      .toFile(thumbnailPath);
    return true;
  } catch (error) {
    console.error('Error generating thumbnail:', error);
    return false;
  }
}

// Handle getting photos from the specified directory
ipcMain.handle('get-photos', async () => {
  try {
    const photosPath = path.join(os.homedir(), 'Desktop', 'local_photos');
    
    // Check if directory exists
    if (!fs.existsSync(photosPath)) {
      console.log(`Directory ${photosPath} does not exist`);
      return [];
    }

    // Read directory contents
    const files = fs.readdirSync(photosPath);
    
    // Filter for image files
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'];
    const imageFiles = files.filter(file => {
      const ext = path.extname(file).toLowerCase();
      return imageExtensions.includes(ext);
    });

    // Return full paths to the images with file stats
    const photos = await Promise.all(imageFiles.map(async (file) => {
      const fullPath = path.join(photosPath, file);
      try {
        const stats = fs.statSync(fullPath);
        return {
          name: file,
          path: fullPath,
          size: stats.size,
          modified: stats.mtime
        };
      } catch (error) {
        console.error(`Error getting stats for ${file}:`, error);
        return null;
      }
    }));

    return photos.filter(photo => photo !== null);
  } catch (error) {
    console.error('Error reading photos directory:', error);
    return [];
  }
});

// Handle thumbnail generation
ipcMain.handle('generate-thumbnail', async (event, imagePath, thumbnailSize = 300) => {
  try {
    const thumbnailsDir = ensureThumbnailsDir();
    const imageHash = Buffer.from(imagePath).toString('base64').replace(/[/+=]/g, '_');
    const thumbnailPath = path.join(thumbnailsDir, `${imageHash}_${thumbnailSize}.jpg`);
    
    // Check if thumbnail already exists
    if (fs.existsSync(thumbnailPath)) {
      return thumbnailPath;
    }
    
    // Generate new thumbnail
    const success = await generateThumbnail(imagePath, thumbnailPath, thumbnailSize);
    if (success) {
      return thumbnailPath;
    } else {
      return null;
    }
  } catch (error) {
    console.error('Error in thumbnail generation:', error);
    return null;
  }
});

// Handle getting image dimensions
ipcMain.handle('get-image-info', async (event, imagePath) => {
  try {
    const metadata = await sharp(imagePath).metadata();
    const stats = fs.statSync(imagePath);
    
    return {
      width: metadata.width,
      height: metadata.height,
      format: metadata.format,
      size: stats.size,
      sizeFormatted: formatFileSize(stats.size)
    };
  } catch (error) {
    console.error('Error getting image info:', error);
    return null;
  }
});

// Format file size for display
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// App event handlers
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
}); 