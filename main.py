#!/usr/bin/env python3
"""
FoodSync - AI-powered food tracking system
Automatically analyzes food photos from Google Drive and logs to Google Sheets
"""

import sys
import time
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import config
from src.utils.logger import setup_logger
from src.utils.image_processor import ImageProcessor
from src.services.google_drive import GoogleDriveService
from src.services.openai_service import OpenAIService
from src.services.google_sheets import GoogleSheetsService

logger = setup_logger()

class FoodSync:
    def __init__(self):
        logger.info("Initializing FoodSync...")
        
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        
        # Initialize services
        self.drive_service = GoogleDriveService()
        self.openai_service = OpenAIService()
        self.sheets_service = GoogleSheetsService()
        self.image_processor = ImageProcessor()
        
        # Ensure Google Sheet has proper headers
        self.sheets_service.ensure_headers()
        
        logger.info("FoodSync initialized successfully")
    
    def process_photo(self, file_info):
        """Process a single photo"""
        logger.info(f"Processing photo: {file_info['name']}")
        
        try:
            # Check if image format is supported
            if not self.image_processor.is_supported_format(file_info['name']):
                logger.warning(f"Unsupported format: {file_info['name']}")
                return None
            
            # Download the file
            logger.debug(f"Downloading file {file_info['id']}")
            file_data = self.drive_service.download_file(file_info['id'], file_info['name'])
            
            if not file_data:
                logger.error(f"Failed to download {file_info['name']}")
                return None
            
            # Process image (convert to JPEG, resize if needed)
            processed_image = self.image_processor.process_image(file_data, file_info['name'])
            
            if not processed_image:
                logger.error(f"Failed to process image {file_info['name']}")
                return None
            
            # Analyze with OpenAI
            logger.debug(f"Analyzing image with OpenAI Vision")
            food_data = self.openai_service.analyze_and_generate_recipe(processed_image)
            
            if not food_data:
                logger.info(f"No food detected in {file_info['name']}")
                self.drive_service.mark_as_processed(file_info['id'])
                return None
            
            # Add photo URL
            food_data['photo_url'] = file_info.get('webViewLink', '')
            
            # Log to Google Sheets
            logger.debug(f"Logging to Google Sheets")
            if self.sheets_service.add_food_entry(food_data):
                logger.info(f"Successfully processed: {file_info['name']} - {food_data['food_name']}")
                self.drive_service.mark_as_processed(file_info['id'])
                return food_data
            else:
                logger.error(f"Failed to log to sheets: {file_info['name']}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing photo {file_info['name']}: {e}", exc_info=True)
            return None
    
    def run_once(self, hours_back=24):
        """Run the sync process once"""
        logger.info(f"Checking for photos from the last {hours_back} hours")
        
        # Get recent photos
        photos = self.drive_service.get_recent_photos(hours_back=hours_back)
        
        if not photos:
            logger.info("No new photos found")
            return
        
        logger.info(f"Found {len(photos)} photos to process")
        
        # Process each photo
        processed_count = 0
        for photo in photos:
            result = self.process_photo(photo)
            if result:
                processed_count += 1
        
        logger.info(f"Processed {processed_count} food photos")
    
    def run_monitor(self, interval_minutes=None):
        """Run continuous monitoring"""
        interval = interval_minutes or config.CHECK_INTERVAL_MINUTES
        logger.info(f"Starting continuous monitoring (checking every {interval} minutes)")
        
        while True:
            try:
                self.run_once(hours_back=24)
            except Exception as e:
                logger.error(f"Error during monitoring cycle: {e}", exc_info=True)
            
            logger.info(f"Waiting {interval} minutes until next check...")
            time.sleep(interval * 60)

def main():
    parser = argparse.ArgumentParser(description='FoodSync - AI-powered food photo tracker')
    parser.add_argument('--monitor', action='store_true', help='Run in continuous monitoring mode')
    parser.add_argument('--interval', type=int, help='Check interval in minutes (for monitor mode)')
    parser.add_argument('--hours', type=int, default=24, help='Check photos from last N hours')
    
    args = parser.parse_args()
    
    # Create FoodSync instance
    app = FoodSync()
    
    try:
        if args.monitor:
            app.run_monitor(interval_minutes=args.interval)
        else:
            app.run_once(hours_back=args.hours)
    except KeyboardInterrupt:
        logger.info("Shutting down FoodSync...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()