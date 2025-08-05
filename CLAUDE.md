# FoodSync Codebase Guide

## Project Overview
FoodSync is an AI-powered food tracking system that monitors Google Drive for food photos, analyzes them with OpenAI Vision, generates recipes, and logs everything to Google Sheets.

## Project Structure
```
foodsync/
├── main.py                      # Entry point, orchestrates the workflow
├── src/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── google_drive.py     # Google Drive API integration
│   │   ├── google_sheets.py    # Google Sheets API integration
│   │   └── openai_service.py   # OpenAI Vision & recipe generation
│   └── utils/
│       ├── __init__.py
│       ├── config.py           # Environment configuration loader
│       ├── image_processor.py  # Image format conversion & processing
│       └── logger.py           # Logging configuration
├── config/
│   └── service-account-key.json # Google service account credentials
├── data/
│   └── processed_files.json    # Tracks processed file IDs
├── logs/                       # Daily log files
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
```

## Key Components

### 1. Main Orchestrator (`main.py`)
- **Class**: `FoodSync`
- **Key Methods**:
  - `run()`: Single execution of the workflow
  - `monitor()`: Continuous monitoring mode
  - `process_photos()`: Core workflow coordination
- **CLI Arguments**:
  - `--monitor`: Enable continuous monitoring
  - `--interval`: Minutes between checks (default: 5)
  - `--hours`: Look back N hours for photos (default: 24)
  - `--limit`: Max photos per run (default: 10)

### 2. Google Drive Service (`src/services/google_drive.py`)
- **Class**: `GoogleDriveService`
- **Key Methods**:
  - `get_recent_photos()`: Fetches photos from last N hours
  - `download_photo()`: Downloads photo as bytes
  - `is_image_file()`: Validates supported formats
- **Supported Formats**: HEIC, HEIF, JPG, JPEG, PNG, BMP, GIF, WEBP

### 3. OpenAI Service (`src/services/openai_service.py`)
- **Class**: `OpenAIService`
- **Key Methods**:
  - `analyze_food_photo()`: Detects food in image
  - `generate_recipe()`: Creates recipe for detected food
- **Model**: GPT-4o-mini with vision capabilities
- **Returns**: `None` if no food detected

### 4. Google Sheets Service (`src/services/google_sheets.py`)
- **Class**: `GoogleSheetsService`
- **Key Methods**:
  - `setup_sheet()`: Creates headers if needed
  - `log_food_entry()`: Logs single entry
  - `log_batch_entries()`: Logs multiple entries
- **Sheet Format**: Date | Food Name | Recipe | Photo URL

### 5. Image Processor (`src/utils/image_processor.py`)
- **Class**: `ImageProcessor`
- **Key Methods**:
  - `process_image()`: Main processing pipeline
  - `convert_heic_to_jpeg()`: HEIC format conversion
  - `resize_image()`: Resizes to max 1920x1080
- **Purpose**: Ensures API compatibility

## Configuration

### Environment Variables (`.env`)
```bash
# Required
GOOGLE_SHEET_ID=y1dKoZeb52gJ-j4lTDMbnfxojkDqd_TqC1rN5t87-8pJY
OPENAI_API_KEY=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

# Optional
GOOGLE_DRIVE_FOLDER_ID=specific-folder-id
LOG_LEVEL=INFO
MAX_PHOTOS_PER_RUN=10
MONITOR_INTERVAL_MINUTES=5
HOURS_LOOKBACK=24
```

### Google Service Account
- Location: `config/service-account-key.json`
- Required APIs:
  - Google Drive API (read access)
  - Google Sheets API (write access)
- Sheet must be shared with service account email

## Data Flow

1. **Photo Detection**
   - Scan Google Drive for recent photos
   - Filter by supported formats
   - Check against processed files list

2. **Image Processing**
   - Download photo bytes
   - Convert HEIC → JPEG if needed
   - Resize large images
   - Convert to RGB format

3. **AI Analysis**
   - Encode image to base64
   - Send to OpenAI Vision API
   - Detect food items
   - Generate recipe if food found

4. **Data Logging**
   - Format entry with timestamp
   - Log to Google Sheets
   - Update processed files list

## Running the Application

### Single Run
```bash
python main.py
```

### Continuous Monitoring
```bash
python main.py --monitor --interval 5 --hours 24
```

### Debug Mode
```bash
LOG_LEVEL=DEBUG python main.py
```

## Testing Commands
```bash
# Run type checking
mypy foodsync/

# Run linting
pylint foodsync/

# Run tests (if available)
pytest tests/
```

## Common Issues & Solutions

1. **HEIC Format Errors**
   - Install: `pip install pillow-heif`
   - Ensures iPhone photo compatibility

2. **Authentication Errors**
   - Verify service account key exists
   - Check API enablement in Google Cloud
   - Ensure sheet is shared with service account

3. **Rate Limiting**
   - Adjust `MAX_PHOTOS_PER_RUN`
   - Increase `MONITOR_INTERVAL_MINUTES`

## Development Notes

- **Logging**: Check `logs/` directory for detailed execution logs
- **State Management**: `data/processed_files.json` tracks all processed photos
- **Error Handling**: All services include try-catch blocks with logging
- **Modularity**: Each service is independent and testable

## Security Considerations

- Service account key should never be committed
- OpenAI API key must be kept secure
- No sensitive data is logged
- Read-only access to Google Drive

## Future Enhancements

- Add nutritional information extraction
- Support for video analysis
- Integration with fitness tracking apps
- Multi-language recipe generation
- Calorie estimation features