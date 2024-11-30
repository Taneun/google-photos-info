from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from PIL import Image
from PIL.ExifTags import TAGS


# Step 1: Authenticate with Google Photos API
def authenticate_google_photos():
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
    flow = InstalledAppFlow.from_client_secrets_file('my_credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)


# Step 2: Fetch photo metadata from Google Photos album
def fetch_google_photos_metadata(service, album_name):
    albums = service.albums().list().execute().get('albums', [])
    album_id = next((album['id'] for album in albums if album['title'] == album_name), None)
    if not album_id:
        raise ValueError(f"Album '{album_name}' not found.")

    photos = []
    next_page_token = None
    while True:
        response = service.mediaItems().search(body={
            'albumId': album_id,
            'pageToken': next_page_token
        }).execute()
        photos.extend(response.get('mediaItems', []))
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return photos


# Step 3: Extract metadata from local photos
# def extract_metadata(file_path):
#     with Image.open(file_path) as img:
#         exif_data = img.getexif()
#         if exif_data:
#             return {TAGS.get(tag): value for tag, value in exif_data.items()}
#         return None


# Step 4: Match photos
def match_photos(google_photos, local_photos):
    total = len(local_photos)
    matching = 0
    no_matching = 0
    no_match_list = []
    print(f"Matching {total} photos...")
    for photo in local_photos:
        filename = os.path.basename(photo)
        match = next((gp for gp in google_photos if gp['filename'] == filename), None)
        if match:
            true_date = match['mediaMetadata']['creationTime']
            if true_date:
                os.utime(photo, (true_date, true_date)) # todo: change to use PIL
                matching += 1
                continue
        no_matching += 1
        no_match_list.append(photo)
    print(f"Matched {matching}/{total} photos.")
    print(f"Failed to match {no_matching}/{total} photos.")
    print("No match list:")
    for no_photo in no_match_list:
        print(no_photo)



# Main Function
def main():
    album_name = "to download"
    local_photo_dir = "/Users/talneumann/Downloads/downloaded_album"

    service = authenticate_google_photos()
    google_photos = fetch_google_photos_metadata(service, album_name)

    local_photos = [os.path.join(local_photo_dir, f) for f in os.listdir(local_photo_dir)]
    match_photos(google_photos, local_photos)

    # for local, google in matches:
    #     print(f"Matched: {local} -> {google['filename']}")


if __name__ == "__main__":
    main()
