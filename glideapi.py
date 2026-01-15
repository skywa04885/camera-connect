import logging
from pathlib import Path
from typing import Literal, Annotated, Optional, Any
from datetime import datetime, timezone
from config import GLIDE_API_KEY, GLIDE_APP_ID, GLIDE_TABLE_NAME_COLUMN, GLIDE_TABLE_NAME, GLIDE_TABLE_DATE_TIME_COLUMN, \
    GLIDE_TABLE_DEVICE_COLUMN, DEVICE_IDENTIFIER
from pydantic import BaseModel, Field
import mimetypes
import requests

MUTATE_TABLES_URL: str = 'https://api.glideapp.io/api/function/mutateTables'
CREATE_UPLOAD_URL: str = f'https://api.glideapps.com/apps/{GLIDE_APP_ID}/uploads'
COMPLETE_UPLOAD_URL: str = f'https://api.glideapps.com/apps/{GLIDE_APP_ID}/uploads/{{upload_id}}/complete'
AUTHORIZATION_HEADER: tuple[str, str] = 'Authorization', f'Bearer {GLIDE_API_KEY}'
JSON_CONTENT_TYPE_HEADER: tuple[str, str] = 'Content-Type', 'application/json'

logger = logging.getLogger('GlideAPI')


class StartUploadPayload(BaseModel):
    content_type: Annotated[str, Field(serialization_alias='contentType')]
    content_length: Annotated[int, Field(serialization_alias='contentLength')]
    file_name: Annotated[str, Field(serialization_alias='fileName')]


class UploadSlot(BaseModel):
    data: UploadSlotData


class UploadSlotData(BaseModel):
    upload_id: Annotated[str, Field(alias='uploadID')]
    upload_location: Annotated[str, Field(alias='uploadLocation')]


def create_start_upload_headers() -> dict[str, str]:
    headers: dict[str, str] = {}

    headers.update([AUTHORIZATION_HEADER, JSON_CONTENT_TYPE_HEADER])

    return headers


def create_start_upload_json(path: Path) -> dict[str, Any]:
    # Guess the mime type of the file.
    content_type, _ = mimetypes.guess_type(path)
    if content_type is None:
        raise RuntimeError(f'Failed to guess mime-type for {path}')

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
    # Guess the MIME type of the file that will be uploaded.
    content_type, _ = mimetypes.guess_type(path)
    if content_type is None:
        raise RuntimeError(f'Failed to guess mime-type for {path}')

    # Return the headers.
    return {
        'Content-Type': content_type
    }


def upload(upload_location: str, path: Path) -> None:
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


class CompletedUpload(BaseModel):
    data: CompletedUploadData


class CompletedUploadData(BaseModel):
    url: str


def complete(upload_id: str) -> str:
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


class TableMutations(BaseModel):
    app_id: Annotated[str, Field(serialization_alias='appID')] = GLIDE_APP_ID
    mutations: list[TableMutation]


class TableMutation(BaseModel):
    kind: Literal['add-row-to-table'] = 'add-row-to-table'
    table_name: Annotated[str, Field(serialization_alias='tableName')] = GLIDE_TABLE_NAME
    column_values: Annotated[ColumnValues, Field(serialization_alias='columnValues')]


class ColumnValues(BaseModel):
    name: Annotated[str, Field(serialization_alias=GLIDE_TABLE_NAME_COLUMN)]
    date_time: Annotated[str, Field(serialization_alias=GLIDE_TABLE_DATE_TIME_COLUMN)]
    device_id: Annotated[str, Field(serialization_alias=GLIDE_TABLE_DEVICE_COLUMN)] = DEVICE_IDENTIFIER


def create_add_row_json(image_url: str) -> dict[str, Any]:
    column_values = ColumnValues(name=image_url,
                                 date_time=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    table_mutation = TableMutation(column_values=column_values)
    table_mutations = TableMutations(mutations=[table_mutation])

    return table_mutations.model_dump(by_alias=True)


def mutate_table(image_url: str) -> None:
    """
    Mutate the table by adding the given image.
    :param image_url: The URL of the image to add.
    """

    # Create the request headers.
    headers: dict[str, str] = {}
    headers.update([AUTHORIZATION_HEADER, JSON_CONTENT_TYPE_HEADER])

    # Create the request JSON.
    json: dict[str, Any] = create_add_row_json(image_url)

    # Send the request.
    logger.info(f'Sending table mutation request with body {json}')
    response: requests.Response = requests.post(MUTATE_TABLES_URL, headers=headers, json=json)

    # Make sure the request was successful.
    if response.status_code != 200:
        logger.error(f'Table mutation request failed, status code: {response.status_code}')
        raise RuntimeError(f'Table mutation request failed, status code: {response.status_code}')
