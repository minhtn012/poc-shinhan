import os

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session

from app.database import get_session
from app.services import template_service

router = APIRouter(prefix="/api/templates", tags=["templates"])


# --- Pydantic schemas (camelCase via alias) ---

class TemplateCreate(BaseModel):
    name: str
    description: str | None = None


class TemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class FieldRead(BaseModel):
    id: str
    name: str
    color: str
    bbox: dict


class VersionRead(BaseModel):
    id: str
    templateId: str
    version: str
    status: str
    imageUrl: str
    fields: list[FieldRead]
    createdAt: str


class TemplateListItem(BaseModel):
    id: str
    name: str
    description: str | None
    activeVersionId: str | None
    versionCount: int
    createdAt: str


class TemplateDetail(BaseModel):
    id: str
    name: str
    description: str | None
    activeVersionId: str | None
    versions: list[VersionRead]
    createdAt: str


class FieldsUpdate(BaseModel):
    fields: list[dict]


# --- Endpoints ---

@router.get("", response_model=list[TemplateListItem])
def list_templates(session: Session = Depends(get_session)):
    return template_service.list_templates(session)


@router.post("", status_code=201)
def create_template(body: TemplateCreate, session: Session = Depends(get_session)):
    return template_service.create_template(session, body.name, body.description)


@router.get("/{template_id}", response_model=TemplateDetail)
def get_template(template_id: str, session: Session = Depends(get_session)):
    result = template_service.get_template(session, template_id)
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.put("/{template_id}")
def update_template(template_id: str, body: TemplateUpdate, session: Session = Depends(get_session)):
    result = template_service.update_template(session, template_id, body.name, body.description)
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: str, session: Session = Depends(get_session)):
    if not template_service.delete_template(session, template_id):
        raise HTTPException(status_code=404, detail="Template not found")


# --- Version endpoints ---

@router.get("/{template_id}/versions", response_model=list[VersionRead])
def list_versions(template_id: str, session: Session = Depends(get_session)):
    return template_service.list_versions(session, template_id)


@router.post("/{template_id}/versions", status_code=201)
async def create_version(
    template_id: str,
    image: UploadFile,
    version: str = Form(...),
    fields: str = Form("[]"),
    session: Session = Depends(get_session),
):
    ext = os.path.splitext(image.filename or "img.png")[1]
    content = await image.read()
    result = template_service.create_version(session, template_id, version, content, ext, fields)
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.get("/{template_id}/suggest-version")
def suggest_version(template_id: str, session: Session = Depends(get_session)):
    return template_service.suggest_version(session, template_id)


# --- Version-level endpoints (no template prefix) ---

version_router = APIRouter(prefix="/api/versions", tags=["versions"])


@version_router.put("/{version_id}/activate")
def activate_version(version_id: str, session: Session = Depends(get_session)):
    result = template_service.activate_version(session, version_id)
    if not result:
        raise HTTPException(status_code=404, detail="Version not found")
    return result


@version_router.put("/{version_id}/fields")
def update_fields(version_id: str, body: FieldsUpdate, session: Session = Depends(get_session)):
    result = template_service.update_fields(session, version_id, body.fields)
    if not result:
        raise HTTPException(status_code=404, detail="Version not found")
    return result
