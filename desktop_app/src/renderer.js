const { ipcRenderer } = require('electron');
const path = require('path');

let allPhotos = [];
let filteredPhotos = [];
let displayedPhotos = [];
let currentPage = 0;
const PHOTOS_PER_PAGE = 50;
const FIXED_THUMBNAIL_SIZE = 250; // Fixed thumbnail size
let isGeneratingThumbnails = false;

// DOM elements
const gallery = document.getElementById('gallery');
const loading = document.getElementById('loading');
const noPhotos = document.getElementById('no-photos');
const photoCount = document.getElementById('photo-count');
const searchInput = document.getElementById('search-input');
const refreshBtn = document.getElementById('refresh-btn');
const modal = document.getElementById('photo-modal');
const modalImage = document.getElementById('modal-image');
const modalFilename = document.getElementById('modal-filename');
const modalPath = document.getElementById('modal-path');
const closeModal = document.querySelector('.close');
const loadMoreBtn = document.getElementById('load-more-btn');
const paginationInfo = document.getElementById('pagination-info');

// Intersection Observer for lazy loading
let imageObserver;

// Initialize the app
async function init() {
    setupIntersectionObserver();
    await loadPhotos();
    setupEventListeners();
}

// Setup Intersection Observer for lazy loading
function setupIntersectionObserver() {
    imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const photoItem = entry.target;
                const imagePath = photoItem.dataset.imagePath;
                
                if (imagePath && !photoItem.dataset.loaded) {
                    loadThumbnail(photoItem, imagePath, FIXED_THUMBNAIL_SIZE);
                    imageObserver.unobserve(photoItem);
                }
            }
        });
    }, {
        rootMargin: '50px'
    });
}

// Load photos from the directory
async function loadPhotos() {
    try {
        loading.style.display = 'flex';
        gallery.style.display = 'none';
        noPhotos.style.display = 'none';
        loadMoreBtn.style.display = 'none';
        
        // Get photos from main process
        allPhotos = await ipcRenderer.invoke('get-photos');
        filteredPhotos = [...allPhotos];
        currentPage = 0;
        displayedPhotos = [];
        
        loading.style.display = 'none';
        
        if (allPhotos.length === 0) {
            noPhotos.style.display = 'flex';
            photoCount.textContent = 'No photos found';
            paginationInfo.textContent = '';
        } else {
            gallery.style.display = 'grid';
            photoCount.textContent = `${allPhotos.length} photo${allPhotos.length !== 1 ? 's' : ''} found`;
            loadNextPage();
        }
    } catch (error) {
        console.error('Error loading photos:', error);
        loading.style.display = 'none';
        noPhotos.style.display = 'flex';
        photoCount.textContent = 'Error loading photos';
        paginationInfo.textContent = '';
    }
}

// Load the next page of photos
function loadNextPage() {
    const startIndex = currentPage * PHOTOS_PER_PAGE;
    const endIndex = Math.min(startIndex + PHOTOS_PER_PAGE, filteredPhotos.length);
    const newPhotos = filteredPhotos.slice(startIndex, endIndex);
    
    if (newPhotos.length > 0) {
        displayedPhotos = [...displayedPhotos, ...newPhotos];
        renderPhotos();
        currentPage++;
        
        // Update pagination info
        const totalDisplayed = displayedPhotos.length;
        const totalPhotos = filteredPhotos.length;
        paginationInfo.textContent = `Showing ${totalDisplayed} of ${totalPhotos} photos`;
        
        // Show/hide load more button
        if (totalDisplayed < totalPhotos) {
            loadMoreBtn.style.display = 'block';
            loadMoreBtn.textContent = `Load More (${Math.min(PHOTOS_PER_PAGE, totalPhotos - totalDisplayed)} more)`;
        } else {
            loadMoreBtn.style.display = 'none';
        }
    }
}

// Reset pagination and start fresh
function resetPagination() {
    currentPage = 0;
    displayedPhotos = [];
    gallery.innerHTML = '';
    loadMoreBtn.style.display = 'none';
    loadNextPage();
}

// Render photos in the gallery
function renderPhotos() {
    // Only render new photos, not all displayed photos
    const startIndex = displayedPhotos.length - (currentPage > 0 ? PHOTOS_PER_PAGE : displayedPhotos.length);
    const newPhotos = displayedPhotos.slice(Math.max(0, startIndex));
    
    newPhotos.forEach((photo, index) => {
        const photoItem = createPhotoItem(photo, startIndex + index);
        gallery.appendChild(photoItem);
        // Observe the photo item for lazy loading
        imageObserver.observe(photoItem);
    });
}

// Create a photo item element with lazy loading
function createPhotoItem(photo, index) {
    const photoItem = document.createElement('div');
    photoItem.className = 'photo-item';
    photoItem.style.width = `${FIXED_THUMBNAIL_SIZE}px`;
    photoItem.dataset.imagePath = photo.path;
    
    // Create loading placeholder with photo info
    photoItem.innerHTML = `
        <div class="photo-loading">
            <div class="loading-spinner-small"></div>
            <div class="loading-text">Generating thumbnail...</div>
        </div>
        <div class="photo-info">
            <div class="photo-name">${photo.name}</div>
            <div class="photo-size">${formatFileSize(photo.size)}</div>
        </div>
    `;
    
    // Add click handler for modal (will work even before image loads)
    photoItem.addEventListener('click', () => {
        openModal(photo);
    });
    
    return photoItem;
}

// Load thumbnail for a photo item
async function loadThumbnail(photoItem, imagePath, thumbnailSize) {
    try {
        photoItem.dataset.loaded = 'true';
        
        // Generate or get cached thumbnail
        const thumbnailPath = await ipcRenderer.invoke('generate-thumbnail', imagePath, parseInt(thumbnailSize));
        
        if (thumbnailPath) {
            // Create image element
            const img = document.createElement('img');
            img.src = `file://${thumbnailPath}`;
            img.alt = path.basename(imagePath);
            
            // Handle image load
            img.onload = () => {
                const loadingDiv = photoItem.querySelector('.photo-loading');
                if (loadingDiv) {
                    loadingDiv.replaceWith(img);
                }
            };
            
            // Handle image error
            img.onerror = () => {
                const loadingDiv = photoItem.querySelector('.photo-loading');
                if (loadingDiv) {
                    loadingDiv.innerHTML = '<div class="photo-error">❌<br>Thumbnail failed</div>';
                    loadingDiv.className = 'photo-error';
                }
            };
        } else {
            // Fallback to original image if thumbnail generation fails
            const img = document.createElement('img');
            img.src = `file://${imagePath}`;
            img.alt = path.basename(imagePath);
            
            img.onload = () => {
                const loadingDiv = photoItem.querySelector('.photo-loading');
                if (loadingDiv) {
                    loadingDiv.replaceWith(img);
                }
            };
            
            img.onerror = () => {
                const loadingDiv = photoItem.querySelector('.photo-loading');
                if (loadingDiv) {
                    loadingDiv.innerHTML = '<div class="photo-error">❌<br>Failed to load</div>';
                    loadingDiv.className = 'photo-error';
                }
            };
        }
    } catch (error) {
        console.error('Error loading thumbnail:', error);
        const loadingDiv = photoItem.querySelector('.photo-loading');
        if (loadingDiv) {
            loadingDiv.innerHTML = '<div class="photo-error">❌<br>Error loading</div>';
            loadingDiv.className = 'photo-error';
        }
    }
}

// Open photo in modal with image info
async function openModal(photo) {
    modalImage.src = `file://${photo.path}`;
    modalFilename.textContent = photo.name;
    modalPath.textContent = photo.path;
    modal.style.display = 'block';
    
    // Get and display image info
    try {
        const imageInfo = await ipcRenderer.invoke('get-image-info', photo.path);
        if (imageInfo) {
            modalPath.textContent = `${photo.path} • ${imageInfo.width}×${imageInfo.height} • ${imageInfo.sizeFormatted}`;
        }
    } catch (error) {
        console.error('Error getting image info:', error);
    }
    
    // Prevent body scrolling when modal is open
    document.body.style.overflow = 'hidden';
}

// Close modal
function closeModalHandler() {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Filter photos based on search input
async function filterPhotos() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    if (searchTerm === '') {
        filteredPhotos = [...allPhotos];
    } else {
        try {
            // Show loading state while searching
            photoCount.textContent = 'Searching...';
            
            // Make HTTP request to search endpoint
            const response = await fetch('http://localhost:7100/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: searchTerm })
            });
            
            if (!response.ok) {
                throw new Error(`Search request failed: ${response.status}`);
            }
            
            const searchResults = await response.json();

            console.log(searchResults);
            
            // Extract image paths from matches
            const matchingPaths = new Set();
            if (searchResults.matches && Array.isArray(searchResults.matches)) {
                searchResults.matches.forEach(match => {
                    if (match.path) {
                        matchingPaths.add(match.path);
                    }
                });
            }
            
            console.log(matchingPaths);
            // Filter photos to only include those in the search results
            filteredPhotos = allPhotos.filter(photo => matchingPaths.has(photo.path));
            
        } catch (error) {
            console.error('Search error:', error);
            // Fallback to local filename search if HTTP request fails
            filteredPhotos = allPhotos.filter(photo => 
                photo.name.toLowerCase().includes(searchTerm)
            );
            photoCount.textContent = 'Search service unavailable - using filename search';
            // Reset pagination and load first page of filtered results
            resetPagination();
            return;
        }
    }
    
    // Reset pagination and load first page of filtered results
    if (filteredPhotos.length === 0 && searchTerm !== '') {
        photoCount.textContent = 'No matching photos';
        paginationInfo.textContent = '';
        gallery.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: white; padding: 40px;"><h2>🔍 No photos found</h2><p>Try adjusting your search terms</p></div>';
        loadMoreBtn.style.display = 'none';
    } else {
        photoCount.textContent = `${filteredPhotos.length} photo${filteredPhotos.length !== 1 ? 's' : ''} found`;
        resetPagination();
    }
}

// Format file size helper
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Setup event listeners
function setupEventListeners() {
    // Refresh button
    refreshBtn.addEventListener('click', loadPhotos);
    
    // Load more button
    loadMoreBtn.addEventListener('click', loadNextPage);
    
    // Search input (debounced) - wrap async function
    const debouncedFilter = debounce(async () => {
        await filterPhotos();
    }, 300);
    searchInput.addEventListener('input', debouncedFilter);
    
    // Modal close handlers
    closeModal.addEventListener('click', closeModalHandler);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModalHandler();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModalHandler();
        }
        if (e.key === 'F5' || (e.metaKey && e.key === 'r')) {
            e.preventDefault();
            loadPhotos();
        }
    });
}

// Debounce helper function - updated to handle async functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', init); 