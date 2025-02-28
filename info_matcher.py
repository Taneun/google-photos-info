import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import subprocess
from dateutil import parser
from tqdm import tqdm
import piexif
from PIL import Image
import shutil



# Step 1: Authenticate with Google Photos API
def authenticate_google_photos():
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
    flow = InstalledAppFlow.from_client_secrets_file('my_credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)


# Step 2: Fetch photo metadata from Google Photos album
def fetch_google_photos_metadata(service, album_name, save_to_file=False):
    """
    Fetch metadata of all photos in a Google Photos album.
    :param service:
    :param album_name:
    :param save_to_file:
    :return:
    """
    # check if the metadata is already saved in a file
    albums = service.albums().list().execute().get('albums', [])
    album_id = next((album['id'] for album in albums if album['title'] == album_name), None)
    if not album_id:
        raise ValueError(f"Album '{album_name}' not found.")

    photos = []
    next_page_token = None
    print('Fetching Photos Metadata...')
    while True:
        response = service.mediaItems().search(body={
            'albumId': album_id,
            'pageToken': next_page_token
        }).execute()
        photos.extend(response.get('mediaItems', []))
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    if save_to_file:
        with open('photos_metadata.json', 'w') as f:
            json.dump(photos, f)

    return photos


def match_photos(google_photos, local_photos):
    """
    Match photos by filename and update local photo metadata with Google Photos metadata.
    :param google_photos: List of Google Photos with metadata
    :param local_photos: List of local photo paths
    :return: None
    """
    total = len(local_photos)
    matching = 0
    no_matching = 0
    no_match_list = []
    failed_updates = []

    print(f"Matching {total} photos...")

    # Create a progress bar
    for photo in tqdm(local_photos, desc="Updating photo metadata", unit="photo"):
        filename = os.path.basename(photo)
        match = next((gp for gp in google_photos if gp['filename'] == filename), None)
        if match:
            true_date = match['mediaMetadata'].get('creationTime')
            if true_date:
                try:
                    # Parse the RFC 3339 timestamp
                    parsed_date = parser.parse(true_date)

                    # Update the metadata using piexif
                    change_metadata(photo, parsed_date)

                    # Count as successful
                    matching += 1
                except Exception as e:
                    no_matching += 1
                    failed_updates.append((photo, f"exception: {str(e)}"))
                    no_match_list.append(photo)
                continue

        no_matching += 1
        no_match_list.append(photo)

    # Print summary at the end
    print(f"Matched {matching}/{total} photos.")
    print(f"Failed to match {no_matching}/{total} photos.")

    if failed_updates:
        print("\nPhotos failed during metadata update:")
        for photo, reason in failed_updates[:5]:  # Show only first 5 failures
            print(f"- {photo}: {reason}")
        if len(failed_updates) > 5:
            print(f"... and {len(failed_updates) - 5} more failures")

    if no_match_list and no_match_list != [photo for photo, _ in failed_updates]:
        print("\nPhotos with no matching Google Photos entry:")
        unmatched_count = sum(1 for photo in no_match_list if photo not in [p for p, _ in failed_updates])
        print(f"Total unmatched: {unmatched_count}")
        return no_match_list


def change_metadata(path, date_time):
    """
    Update metadata and file timestamps for various image and video formats.

    :param path: Path to the file
    :param date_time: Datetime object with the desired timestamp
    :return: None
    """
    file_ext = os.path.splitext(path)[1].lower()
    date_time_str = date_time.strftime("%Y:%m:%d %H:%M:%S")

    if file_ext in {".jpg", ".jpeg", ".tiff"}:
        # Handle EXIF metadata for JPEG and TIFF
        exif_dict = piexif.load(path)
        # Ensure EXIF values are strings
        exif_dict['0th'][piexif.ImageIFD.DateTime] = date_time_str.encode("utf-8")
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_time_str.encode("utf-8")
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_time_str.encode("utf-8")
        # Convert problematic integer values to strings
        for key, value in exif_dict["Exif"].items():
            if isinstance(value, int):
                exif_dict["Exif"][key] = str(value).encode("utf-8")

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, path)

    elif file_ext == ".png":
        # PNG does not support EXIF, but metadata can be stored in 'info'
        img = Image.open(path)
        img.info['Creation Time'] = date_time_str
        img.save(path)

    elif file_ext in {".heic", ".heif", ".mp4"}:
        # HEIC and MP4 require ExifTool (external command-line tool)
        cmd = [
            "exiftool",
            "-overwrite_original",
            f"-AllDates={date_time_str}",
            path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    elif file_ext == ".gif":
        # GIF does not support EXIF, only modify file timestamps
        pass  # No internal metadata modification possible

    # Update file modification and access timestamps for all formats
    os.utime(path, (date_time.timestamp(), date_time.timestamp()))

def move_unmatched_photos(photo_paths, destination_folder):
    """
    Moves unmatched photos to a separate folder.

    :param photo_paths: List of file paths for unmatched photos.
    :param destination_folder: Path to the destination folder.
    """
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    for photo in photo_paths:
        try:
            file_name = os.path.basename(photo)
            dest_path = os.path.join(destination_folder, file_name)

            # Move the file
            shutil.move(photo, dest_path)
            print(f"Moved: {photo} -> {dest_path}")

        except Exception as e:
            print(f"Failed to move {photo}: {e}")

# Main Function
def main():
    album_name = "to download"
    local_photo_dir = "/Users/talneumann/Downloads/downloaded_album"
    no_match_folder = "/Users/talneumann/Downloads/downloaded_no_match"
    if not os.path.exists('photos_metadata.json'):
        service = authenticate_google_photos()
        google_photos = fetch_google_photos_metadata(service, album_name, save_to_file=True)
    else:
        with open('photos_metadata.json', 'r') as f:
            google_photos = json.load(f)

    local_photos = [os.path.join(local_photo_dir, f) for f in os.listdir(local_photo_dir)]
    left_with_no_match = match_photos(google_photos, local_photos)
    if left_with_no_match:
        move_unmatched_photos(left_with_no_match, no_match_folder)

if __name__ == "__main__":
    main()
