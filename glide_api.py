import logging
from pathlib import Path
from typing import Any
from datetime import datetime, timezone
import mimetypes
import requests

from config import GLIDE_APP_ID, GLIDE_API_KEY, WEBHOOK_URL, WEBHOOK_TOKEN
from glide_api_models import StartUploadPayload, UploadSlot, CompletedUpload, WebhookData

# URLs used for contacting the API.
MUTATE_TABLES_URL: str = 'https://api.glideapp.io/api/function/mutateTables'
CREATE_UPLOAD_URL: str = f'https://api.glideapps.com/apps/{GLIDE_APP_ID}/uploads'
COMPLETE_UPLOAD_URL: str = f'https://api.glideapps.com/apps/{GLIDE_APP_ID}/uploads/{{upload_id}}/complete'

# Headers that will be used commonly.
AUTHORIZATION_HEADER: tuple[str, str] = 'Authorization', f'Bearer {GLIDE_API_KEY}'
WEBHOOK_AUTHORIZATION_HEADER: tuple[str, str] = 'Authorization', f'Bearer {WEBHOOK_TOKEN}'
JSON_CONTENT_TYPE_HEADER: tuple[str, str] = 'Content-Type', 'application/json'

# Create the logger.
logger = logging.getLogger('GlideAPI')


def guess_content_type(path: Path) -> str:
    content_type, _ = mimetypes.guess_type(path)
    if content_type is None:
        raise RuntimeError(f'Failed to guess content type for {path}')

    return content_type


def create_start_upload_headers() -> dict[str, str]:
    headers: dict[str, str] = {}

    headers.update([AUTHORIZATION_HEADER, JSON_CONTENT_TYPE_HEADER])

    return headers


def create_start_upload_json(path: Path) -> dict[str, Any]:
    # Guess the content type of the file.
    content_type: str = guess_content_type(path)

    # Get the size of the file.
    content_length: int = path.stat().st_size

    # Create the payload of the upload request.
    payload: StartUploadPayload = StartUploadPayload(content_type=content_type, content_length=content_length,
                                                     file_name=path.name)

    # Dump the payload as JSON.
    return payload.model_dump(by_alias=True)


def start_upload(path: Path) -> tuple[str, str]:
    # Create the start upload headers.
    headers: dict[str, str] = create_start_upload_headers()

    # Create the start upload JSON.
    json: dict[str, str] = create_start_upload_json(path)

    # Send the request.
    response: requests.Response = requests.post(CREATE_UPLOAD_URL, headers=headers, json=json)

    # Make sure the upload was successful.
    if response.status_code != 200:
        logger.error(f'Failed to create upload for {path}, status code: {response.status_code}')
        raise RuntimeError(f'Failed to create upload for {path}, status code: {response.status_code}')

    # Get the JSON from the response.
    json: dict[str, Any] = response.json()

    # Validate the response into the upload slot.
    upload_slot: UploadSlot = UploadSlot.model_validate(json)

    # Return the upload ID upload location.
    return upload_slot.data.upload_id, upload_slot.data.upload_location


def create_upload_headers(path: Path) -> dict[str, str]:
    # Guess the content type of the file.
    content_type: str = guess_content_type(path)

    # Return the headers.
    return {
        'Content-Type': content_type
    }


def upload_file(upload_location: str, path: Path) -> None:
    # Create the headers for the upload.
    headers: dict[str, str] = create_upload_headers(path)

    # Send the request.
    with path.open('rb') as file:
        logger.info(f'Uploading file {path} to location {upload_location}')
        response: requests.Response = requests.put(upload_location, file, headers=headers)

    # Make sure the upload was successful.
    if response.status_code != 200:
        logger.error(f'Failed to upload {path} to location {upload_location}, status code: {response.status_code}')
        raise RuntimeError(
            f'Failed to upload {path} to location {upload_location}, status code: {response.status_code}')


def complete_upload(upload_id: str) -> str:
    """
    Complete the upload that has the given ID.
    :param upload_id: The ID of the upload.
    :return: The URL of the uploaded image.
    """

    # Format the completion url.
    url: str = COMPLETE_UPLOAD_URL.format(upload_id=upload_id)

    # Create the complete headers.
    headers: dict[str, str] = {}
    headers.update([AUTHORIZATION_HEADER])

    # Send the complete upload request.
    logger.info(f'Sending complete upload request for upload {upload_id}')
    response = requests.post(url, headers=headers)

    # Make sure the request was successful.
    if response.status_code != 200:
        logger.error(f'Complete upload request failed for upload {upload_id}, status code: {response.status_code}')
        raise RuntimeError(
            f'Complete upload request failed for upload {upload_id}, status code: {response.status_code}')

    # Get the response JSON.
    json = response.json()

    # Validate the JSON into the completed upload.
    completed_upload = CompletedUpload.model_validate(json)

    # Return the URL.
    return completed_upload.data.url


def trigger_webhook(image_url: str, label: str) -> None:
    # Create the data that is sent to the webhook.
    data: WebhookData = WebhookData(image_url=image_url, label=label)

    # JSON from the data.
    json: dict[str, Any] = data.model_dump(by_alias=True)

    # Create the headers for the webhook.
    headers: dict[str, str] = {}
    headers.update([WEBHOOK_AUTHORIZATION_HEADER, JSON_CONTENT_TYPE_HEADER])

    # Send the request.
    logger.info(f'Triggering webhook with image url {image_url}')
    response = requests.post(WEBHOOK_URL, headers=headers, json=json)

    # Make sure the request was successful.
    if response.status_code != 200:
        logger.error(f'Webhook trigger for image url {image_url} failed, status code: {response.status_code}')
        raise RuntimeError(
            f'Webhook trigger for image url {image_url} failed, status code: {response.status_code}')
