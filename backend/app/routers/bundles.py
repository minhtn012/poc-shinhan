from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.database import get_session
from app.services import bundle_service

router = APIRouter(prefix="/api/bundles", tags=["bundles"])


class BundleCreate(BaseModel):
    name: str
    description: str | None = None
    templateIds: list[str] = []


class BundleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    templateIds: list[str] | None = None


class BundleItemRead(BaseModel):
    id: str
    templateId: str
    templateName: str
    activeVersionId: str | None
    sortOrder: int


class BundleListItem(BaseModel):
    id: str
    name: str
    description: str | None
    templateCount: int
    createdAt: str


class BundleDetailRead(BaseModel):
    id: str
    name: str
    description: str | None
    templateCount: int
    items: list[BundleItemRead]
    createdAt: str


@router.get("", response_model=list[BundleListItem])
def list_bundles(session: Session = Depends(get_session)):
    return bundle_service.list_bundles(session)


@router.post("", status_code=201)
def create_bundle(body: BundleCreate, session: Session = Depends(get_session)):
    try:
        return bundle_service.create_bundle(session, body.name, body.description, body.templateIds)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{bundle_id}", response_model=BundleDetailRead)
def get_bundle(bundle_id: str, session: Session = Depends(get_session)):
    result = bundle_service.get_bundle(session, bundle_id)
    if not result:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return result


@router.put("/{bundle_id}")
def update_bundle(bundle_id: str, body: BundleUpdate, session: Session = Depends(get_session)):
    try:
        result = bundle_service.update_bundle(session, bundle_id, body.name, body.description, body.templateIds)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return result


@router.delete("/{bundle_id}", status_code=204)
def delete_bundle(bundle_id: str, session: Session = Depends(get_session)):
    if not bundle_service.delete_bundle(session, bundle_id):
        raise HTTPException(status_code=404, detail="Bundle not found")
