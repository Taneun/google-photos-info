# Google Photos Metadata Updater

## Overview
This script fetches photo metadata from a specified Google Photos album and updates the timestamps of matching local photos accordingly. It supports various image formats and utilizes ExifTool for updating metadata of HEIC and MP4 files.

## Features
- Authenticates with Google Photos API to access albums.
- Fetches metadata (creation time) of photos from a specified album.
- Matches local photos by filename and updates their timestamps.
- Supports JPEG, PNG, HEIC, HEIF, MP4, and GIF formats.
- Moves unmatched photos to a separate folder for manual review.

## Requirements
- Python 3.x
- Required libraries:
  - `google-auth-oauthlib`
  - `google-auth`
  - `googleapiclient`
  - `tqdm`
  - `dateutil`
  - `piexif`
  - `Pillow`
  - `shutil`
  - `subprocess`
- `exiftool` (for HEIC and MP4 metadata updates)

## Setup
1. Install required Python dependencies:
   ```bash
   pip install google-auth google-auth-oauthlib google-auth-httplib2 googleapiclient tqdm python-dateutil piexif pillow
   ```
2. Download your Google API credentials JSON file and save it as `my_credentials.json`.
3. Ensure `exiftool` is installed on your system (if processing HEIC or MP4 files).

## Usage
1. Update the `album_name`, `local_photo_dir`, and `no_match_folder` variables in `main()` to match your setup.
2. Run the script:
   ```bash
   python script.py
   ```
3. If metadata is already saved (`photos_metadata.json`), the script will load from it instead of fetching again.

## Notes
- This script modifies file metadata and timestamps—use with caution.
- Unmatched photos are moved to a separate folder for manual review.
- Ensure Google Photos API is enabled for your Google Cloud project.

## License
MIT License

