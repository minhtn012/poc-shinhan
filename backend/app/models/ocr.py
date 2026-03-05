import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class OcrJob(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    template_version_id: str = Field(foreign_key="templateversion.id")
    bundle_id: Optional[str] = Field(default=None, foreign_key="bundle.id")
    template_name: str = ""
    image_path: str = ""
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OcrFieldResult(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="ocrjob.id")
    field_id: str = ""
    field_name: str = ""
    value: str = ""
    confidence: float = 0.0
    edited: bool = False
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
