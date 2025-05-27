/**
 * Utility functions for image processing
 */

/**
 * Resize an image file to a maximum dimension while maintaining aspect ratio
 * @param file - The image file to resize
 * @param maxDimension - Maximum width or height (default: 512)
 * @returns Promise that resolves to a resized File object
 */
export const resizeImage = (file: File, maxDimension: number = 512): Promise<File> => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    if (!ctx) {
      reject(new Error('Failed to get canvas context'));
      return;
    }

    img.onload = () => {
      // Calculate new dimensions while maintaining aspect ratio
      let { width, height } = img;
      
      if (width > height) {
        if (width > maxDimension) {
          height = (height * maxDimension) / width;
          width = maxDimension;
        }
      } else {
        if (height > maxDimension) {
          width = (width * maxDimension) / height;
          height = maxDimension;
        }
      }

      // Set canvas size to new dimensions
      canvas.width = width;
      canvas.height = height;

      // Draw the resized image on canvas
      ctx.drawImage(img, 0, 0, width, height);

      // Convert canvas to blob
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Failed to create blob from canvas'));
            return;
          }

          // Create a new File object with the same name and type
          const resizedFile = new File([blob], file.name, {
            type: file.type,
            lastModified: Date.now()
          });

          resolve(resizedFile);
        },
        file.type,
        0.9 // Quality for JPEG compression
      );
    };

    img.onerror = () => {
      reject(new Error('Failed to load image'));
    };

    // Create object URL from file and set as image source
    img.src = URL.createObjectURL(file);
  });
};

/**
 * Resize an image and convert to base64
 * @param file - The image file to resize and convert
 * @param maxDimension - Maximum width or height (default: 512)
 * @returns Promise that resolves to base64 string (without data URL prefix)
 */
export const resizeImageToBase64 = async (file: File, maxDimension: number = 512): Promise<string> => {
  const resizedFile = await resizeImage(file, maxDimension);
  
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(resizedFile);
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        // Remove the data URL prefix and return just the base64 data
        const base64Data = reader.result.split(',')[1];
        resolve(base64Data);
      } else {
        reject(new Error('Failed to convert resized file to base64'));
      }
    };
    reader.onerror = error => reject(error);
  });
}; 