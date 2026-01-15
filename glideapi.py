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
COMPLETE_UPLOAD_URL: str =f'https://api.glideapps.com/apps/{GLIDE_APP_ID}/uploads/{{upload_id}}/complete'
AUTHORIZATION_HEADER: tuple[str, str] = 'Authorization', f'Bearer {GLIDE_API_KEY}'
JSON_CONTENT_TYPE_HEADER: tuple[str, str] = 'Content-Type', 'application/json'

logger = logging.getLogger('GlideAPI')


class UploadSlot(BaseModel):
    data: UploadSlotData


class UploadSlotData(BaseModel):
    upload_id: Annotated[str, Field(alias='uploadID')]
    upload_location: Annotated[str, Field(alias='uploadLocation')]


def create_upload(path: Path) -> tuple[str, str]:
    content_type, _ = mimetypes.guess_type(path)
    content_length = path.stat().st_size
    assert content_type is not None

    headers: dict[str, str] = {}
    headers.update([AUTHORIZATION_HEADER, JSON_CONTENT_TYPE_HEADER])

    json: dict[str, str] = {
        'contentType': content_type,
        'contentLength': content_length,
        'fileName': path.name
    }

    response = requests.post(CREATE_UPLOAD_URL, headers=headers, json=json)
    assert response.status_code == 200

    json = response.json()

    data = json['data']
    assert isinstance(data, dict)

    upload_id = data['uploadID']
    assert isinstance(upload_id, str)

    upload_location = data['uploadLocation']
    assert isinstance(upload_location, str)

    return upload_id, upload_location


def upload(upload_location: str, path: Path) -> None:
    content_type, _ = mimetypes.guess_type(path)
    assert content_type is not None

    headers: dict[str, str] = {
        'Content-Type': content_type
    }

    with path.open('rb') as file:
        response = requests.put(upload_location, file, headers=headers)

    assert response.status_code == 200


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
    if response.status_code != 200:
        logger.error(f'Complete upload request failed for upload {upload_id}, status code: {response.status_code}')
        raise RuntimeError(f'Complete upload request failed for upload {upload_id}, status code: {response.status_code}')

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
    # Create the request headers.
    headers: dict[str, str] = {}
    headers.update([AUTHORIZATION_HEADER, JSON_CONTENT_TYPE_HEADER])

    # Create the request JSON.
    json: dict[str, Any] = create_add_row_json(image_url)

    # Send the request.
    logger.info(f'Sending table mutation request with body {json}')
    response: requests.Response = requests.post(MUTATE_TABLES_URL, headers=headers, json=json)
    if response.status_code != 200:
        logger.error(f'Table mutation request failed, status code: {response.status_code}')
        raise RuntimeError(f'Table mutation request failed, status code: {response.status_code}')
