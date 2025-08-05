import io
import logging
from PIL import Image
from typing import Optional, BinaryIO

logger = logging.getLogger(__name__)

# Try to register HEIF opener, but handle gracefully if it fails
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
    logger.info("HEIF support enabled")
except Exception as e:
    HEIF_SUPPORT = False
    logger.warning(f"HEIF support unavailable: {e}")

class ImageProcessor:
    """Handle image processing and format conversion"""
    
    SUPPORTED_FORMATS = {'.heic', '.heif', '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    MAX_SIZE = (1920, 1080)  # Maximum dimensions for processing
    
    @staticmethod
    def process_image(image_data: BinaryIO, filename: str) -> Optional[bytes]:
        """
        Process image data and convert to JPEG format for API compatibility
        
        Args:
            image_data: Binary image data
            filename: Original filename (used to determine format)
            
        Returns:
            Processed image as JPEG bytes, or None if processing fails
        """
        file_ext = filename.lower().split('.')[-1]
        
        # Check if it's a HEIC file and we don't have HEIF support
        if file_ext in ['heic', 'heif'] and not HEIF_SUPPORT:
            logger.error(f"HEIC/HEIF file {filename} cannot be processed - pillow-heif not properly installed")
            return None
        
        try:
            # Ensure we're at the beginning of the stream
            image_data.seek(0)
            
            # For HEIC files, try multiple approaches
            if file_ext in ['heic', 'heif']:
                image = ImageProcessor._open_heic_image(image_data, filename)
            else:
                image = Image.open(image_data)
            
            if image is None:
                return None
            
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Resize if too large
            if image.width > ImageProcessor.MAX_SIZE[0] or image.height > ImageProcessor.MAX_SIZE[1]:
                image.thumbnail(ImageProcessor.MAX_SIZE, Image.Resampling.LANCZOS)
                logger.info(f"Resized image {filename} to {image.size}")
            
            # Save as JPEG
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            return output.read()
            
        except Exception as e:
            logger.error(f"Error processing image {filename}: {e}")
            return None
    
    @staticmethod
    def _open_heic_image(image_data: BinaryIO, filename: str):
        """Try multiple approaches to open HEIC images"""
        
        # First, check the file signature
        image_data.seek(0)
        first_bytes = image_data.read(20)
        logger.info(f"HEIC file {filename} signature: {first_bytes}")
        
        import tempfile
        import os
        
        approaches = [
            ("Direct PIL", lambda: Image.open(image_data)),
            ("Bytes first", lambda: Image.open(io.BytesIO(image_data.read()))),
            ("Reset and retry", lambda: (image_data.seek(0), Image.open(image_data))[1]),
            ("Force format", lambda: Image.open(image_data, formats=['HEIF'])),
            ("Temp file", lambda: ImageProcessor._open_via_temp_file(image_data, filename)),
        ]
        
        for approach_name, approach_func in approaches:
            try:
                image_data.seek(0)
                image = approach_func()
                logger.info(f"Successfully opened HEIC {filename} using {approach_name}")
                return image
            except Exception as e:
                logger.error(f"{approach_name} failed for {filename}: {e}")
                continue
        
        logger.error(f"All approaches failed for HEIC file {filename}")
        return None
    
    @staticmethod
    def _open_via_temp_file(image_data: BinaryIO, filename: str):
        """Try opening HEIC file via temporary file on disk"""
        import tempfile
        import os
        
        image_data.seek(0)
        data = image_data.read()
        
        # Create temp file with proper extension
        file_ext = filename.lower().split('.')[-1]
        with tempfile.NamedTemporaryFile(suffix=f'.{file_ext}', delete=False) as temp_file:
            temp_file.write(data)
            temp_path = temp_file.name
        
        try:
            image = Image.open(temp_path)
            # Load the image into memory before deleting temp file
            image.load()
            os.unlink(temp_path)
            return image
        except Exception as e:
            os.unlink(temp_path)
            raise e
    
    @staticmethod
    def is_supported_format(filename: str) -> bool:
        """Check if file format is supported"""
        file_ext = filename.lower().split('.')[-1]
        return f'.{file_ext}' in ImageProcessor.SUPPORTED_FORMATS
    
    @staticmethod
    def get_image_info(image_data: BinaryIO) -> dict:
        """Get basic information about an image"""
        try:
            image = Image.open(image_data)
            return {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height
            }
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {}