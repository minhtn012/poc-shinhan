import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class Template(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = ""
    description: Optional[str] = None
    active_version_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TemplateVersion(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    template_id: str = Field(foreign_key="template.id")
    version: str = ""
    status: str = "active"
    image_path: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TemplateField(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    version_id: str = Field(foreign_key="templateversion.id")
    name: str = ""
    color: str = "#2196F3"
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
