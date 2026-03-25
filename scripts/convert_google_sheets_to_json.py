#!/usr/bin/env python3
"""
Script to convert Google Sheets data to JSON files.
Each sheet will be saved as a separate JSON file with the sheet name as filename.
"""

import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration
GOOGLE_SHEET_ID = "1GRLdIr0ONXKTGWxPqyJW9vgcwgaYkU8YdN6eAoVPAeQ"
OUTPUT_DIR = "/home/aseps/MCP/storage/admin_data/korespondensi"

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def get_google_credentials():
    """Get Google credentials from service account file or environment."""
    # Try to get credentials from environment variable
    credentials_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if credentials_json:
        credentials_info = json.loads(credentials_json)
        return Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
    
    # Try to find service account file
    service_account_file = os.path.join(os.path.dirname(__file__), 'service_account.json')
    if os.path.exists(service_account_file):
        return Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
    
    raise Exception("Google credentials not found. Please set GOOGLE_SERVICE_ACCOUNT_JSON environment variable or create service_account.json file.")

def convert_sheet_to_json(sheet, output_dir):
    """Convert a single sheet to JSON format."""
    sheet_name = sheet.title
    print(f"Processing sheet: {sheet_name}")
    
    # Get all values from the sheet
    values = sheet.get_all_values()
    
    if not values:
        print(f"Warning: Sheet '{sheet_name}' is empty")
        return
    
    # Extract header and data rows
    header = values[0]
    data_rows = values[1:]
    
    # Convert to structured format
    structured_data = []
    for row in data_rows:
        # Skip empty rows
        if not any(row):
            continue
        
        row_data = {}
        for i, header_name in enumerate(header):
            # Handle empty header names
            if not header_name.strip():
                header_name = f"Column_{i+1}"
            
            # Get value, handle empty cells
            value = row[i] if i < len(row) else ""
            
            # Convert "null" string to empty string
            if isinstance(value, str) and value.lower() == "null":
                value = ""
            
            row_data[header_name] = value
        
        structured_data.append(row_data)
    
    # Create output data structure
    output_data = {
        "spreadsheet_id": GOOGLE_SHEET_ID,
        "sheet_name": sheet_name,
        "range": f"{sheet_name}!A1:Z1000",  # Approximate range
        "synced_at": datetime.now().isoformat(),
        "total_rows": len(structured_data),
        "header": header,
        "data": structured_data
    }
    
    # Create safe filename from sheet name
    safe_filename = sheet_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{safe_filename}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(structured_data)} rows to {filepath}")
    return filepath

def main():
    """Main function to convert all sheets to JSON."""
    print("Starting Google Sheets to JSON conversion...")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        # Authenticate with Google Sheets
        print("Authenticating with Google Sheets...")
        credentials = get_google_credentials()
        client = gspread.authorize(credentials)
        
        # Open the spreadsheet
        print(f"Opening spreadsheet: {GOOGLE_SHEET_ID}")
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        # Get all worksheets
        worksheets = spreadsheet.worksheets()
        print(f"Found {len(worksheets)} sheets")
        
        # Process each sheet
        processed_files = []
        for worksheet in worksheets:
            try:
                filepath = convert_sheet_to_json(worksheet, OUTPUT_DIR)
                if filepath:
                    processed_files.append(filepath)
            except Exception as e:
                print(f"Error processing sheet '{worksheet.title}': {e}")
                continue
        
        print(f"\nConversion complete! Processed {len(processed_files)} sheets:")
        for filepath in processed_files:
            print(f"  - {os.path.basename(filepath)}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use this script, you need to:")
        print("1. Create a Google Cloud project and enable Google Sheets API")
        print("2. Create a service account and download the JSON key file")
        print("3. Share your Google Sheet with the service account email")
        print("4. Set the GOOGLE_SERVICE_ACCOUNT_JSON environment variable or place service_account.json in the scripts directory")

if __name__ == "__main__":
    main()