import logging
from datetime import datetime
from typing import List, Dict, Any
import gspread
from google.oauth2 import service_account

from ..utils.config import config

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.client = self._authenticate()
        self.sheet = self._get_sheet()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(config.SERVICE_ACCOUNT_FILE),
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            return gspread.authorize(credentials)
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise
    
    def _get_sheet(self):
        """Get the Google Sheet instance"""
        try:
            spreadsheet = self.client.open_by_key(config.GOOGLE_SHEET_ID)
            return spreadsheet.sheet1  # Get first sheet
        except Exception as e:
            logger.error(f"Failed to open Google Sheet: {e}")
            raise
    
    def ensure_headers(self):
        """Ensure the sheet has the correct headers"""
        try:
            # Check if headers exist
            headers = self.sheet.row_values(1)
            expected_headers = ['Date', 'Food Name', 'Recipe', 'Photo URL']
            
            if headers != expected_headers:
                logger.info("Setting up sheet headers")
                self.sheet.update('A1:D1', [expected_headers])
                
                # Format headers
                self.sheet.format('A1:D1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                })
            
            return True
        except Exception as e:
            logger.error(f"Error setting up headers: {e}")
            return False
    
    def add_food_entry(self, food_data: Dict[str, Any]):
        """Add a food entry to the sheet"""
        try:
            # Prepare row data
            row_data = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                food_data.get('food_name', ''),
                food_data.get('recipe', ''),
                food_data.get('photo_url', '')
            ]
            
            # Append row to sheet
            self.sheet.append_row(row_data)
            logger.info(f"Added food entry: {food_data.get('food_name', 'Unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding food entry: {e}")
            return False
    
    def batch_add_entries(self, entries: List[Dict[str, Any]]):
        """Add multiple food entries at once"""
        if not entries:
            return True
        
        try:
            rows = []
            for entry in entries:
                row = [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    entry.get('food_name', ''),
                    entry.get('recipe', ''),
                    entry.get('photo_url', '')
                ]
                rows.append(row)
            
            # Batch update
            self.sheet.append_rows(rows)
            logger.info(f"Added {len(entries)} food entries")
            
            return True
            
        except Exception as e:
            logger.error(f"Error batch adding entries: {e}")
            return False
    
    def get_recent_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent entries from the sheet"""
        try:
            # Get all values
            all_values = self.sheet.get_all_values()
            
            if len(all_values) <= 1:  # Only headers or empty
                return []
            
            # Skip header row and get last 'limit' entries
            data_rows = all_values[1:]
            recent_rows = data_rows[-limit:] if len(data_rows) > limit else data_rows
            
            # Convert to list of dicts
            entries = []
            for row in recent_rows:
                if len(row) >= 4:
                    entries.append({
                        'date': row[0],
                        'food_name': row[1],
                        'recipe': row[2],
                        'photo_url': row[3]
                    })
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting recent entries: {e}")
            return []