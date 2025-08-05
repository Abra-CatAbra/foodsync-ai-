import os
import io
import json
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import logging

from ..utils.config import config

logger = logging.getLogger(__name__)

class GoogleDriveService:
    def __init__(self):
        self.service = self._authenticate()
        self.processed_files = self._load_processed_files()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(config.SERVICE_ACCOUNT_FILE),
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            return build('drive', 'v3', credentials=credentials)
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {e}")
            raise
    
    def _load_processed_files(self):
        """Load list of already processed files"""
        if config.PROCESSED_FILES_DB.exists():
            with open(config.PROCESSED_FILES_DB, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_processed_files(self):
        """Save list of processed files"""
        with open(config.PROCESSED_FILES_DB, 'w') as f:
            json.dump(list(self.processed_files), f)
    
    def get_recent_photos(self, hours_back=24, max_results=None):
        """Get recent photos from Google Drive folder"""
        max_results = max_results or config.MAX_PHOTOS_PER_RUN
        
        # Calculate time threshold
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        time_str = time_threshold.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Build query
        query_parts = [
            f"'{config.GOOGLE_DRIVE_FOLDER_ID}' in parents" if config.GOOGLE_DRIVE_FOLDER_ID else None,
            "trashed = false",
            f"modifiedTime > '{time_str}'",
            "(mimeType contains 'image/')"
        ]
        query = " and ".join([q for q in query_parts if q])
        
        try:
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, webViewLink, modifiedTime)",
                orderBy="modifiedTime desc",
                pageSize=max_results
            ).execute()
            
            files = results.get('files', [])
            
            # Filter out already processed files
            new_files = []
            for file in files:
                if file['id'] not in self.processed_files:
                    new_files.append(file)
            
            logger.info(f"Found {len(new_files)} new photos to process")
            return new_files
            
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return []
    
    def download_file(self, file_id, file_name):
        """Download a file from Google Drive"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_data = io.BytesIO()
            downloader = MediaIoBaseDownload(file_data, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {int(status.progress() * 100)}% complete")
            
            file_data.seek(0)
            return file_data
            
        except HttpError as error:
            logger.error(f"An error occurred downloading file {file_id}: {error}")
            return None
    
    def mark_as_processed(self, file_id):
        """Mark a file as processed"""
        self.processed_files.add(file_id)
        self._save_processed_files()
    
    def get_file_url(self, file_id):
        """Get shareable URL for a file"""
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            return file.get('webViewLink', '')
        except HttpError:
            return ''