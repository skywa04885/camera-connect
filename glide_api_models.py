from typing import Annotated
from pydantic import BaseModel, Field


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


class WebhookData(BaseModel):
    image_url: Annotated[str, Field(serialization_alias='imageUrl')]
    label: str

