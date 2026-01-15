from typing import Annotated, Literal
from pydantic import BaseModel, Field
from config import GLIDE_APP_ID, GLIDE_TABLE_NAME_COLUMN, GLIDE_TABLE_NAME, GLIDE_TABLE_DATE_TIME_COLUMN, \
    GLIDE_TABLE_DEVICE_COLUMN, DEVICE_IDENTIFIER


class StartUploadPayload(BaseModel):
    content_type: Annotated[str, Field(serialization_alias='contentType')]
    content_length: Annotated[int, Field(serialization_alias='contentLength')]
    file_name: Annotated[str, Field(serialization_alias='fileName')]


class UploadSlot(BaseModel):
    data: UploadSlotData


class UploadSlotData(BaseModel):
    upload_id: Annotated[str, Field(alias='uploadID')]
    upload_location: Annotated[str, Field(alias='uploadLocation')]


class CompletedUpload(BaseModel):
    data: CompletedUploadData


class CompletedUploadData(BaseModel):
    url: str


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
