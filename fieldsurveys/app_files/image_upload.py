import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import time


def upload_image_to_imgur(survey_config, image_path):
    client_id = survey_config["imgur_app_id"]
    # Imgur API endpoint
    api_url = "https://api.imgur.com/3/upload"

    headers = {
        "Authorization": f"Client-ID {client_id}",
    }

    with open(image_path, "rb") as file:
        files = {"image": file}
        data = {"type": "file"}

        response = requests.post(api_url, headers=headers, files=files, data=data)

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()["data"]["link"]


def upload_image_to_drive(survey_config, image_path, keyfile_json):
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    creds = service_account.Credentials.from_service_account_file(
        keyfile_json, scopes=SCOPES
    )

    service = build("drive", "v3", credentials=creds)

    folder_id = survey_config["google_folder_id"]
    # Upload the image
    file_metadata = {"parents": [folder_id]}
    media = MediaFileUpload(image_path, mimetype="image/jpeg", resumable=True)
    # Generate a unique name for the file based on current time
    file_name = f"image_{int(time.time())}.jpg"

    file_metadata = {"name": file_name, "parents": [folder_id]}
    media = MediaFileUpload(image_path, mimetype="image/jpeg", resumable=True)

    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    # Set the permissions to make the image publicly accessible
    service.permissions().create(
        fileId=file["id"], body={"role": "reader", "type": "anyone"}
    ).execute()

    # Get the URL of the uploaded image
    file_url = f"https://drive.google.com/uc?id={file['id']}"

    return file_url
