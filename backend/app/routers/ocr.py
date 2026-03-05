import asyncio
import os

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session

from app.database import get_session
from app.services import ocr_service

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


class FieldValueUpdate(BaseModel):
    value: str


class FieldResultRead(BaseModel):
    id: str
    fieldId: str
    fieldName: str
    value: str
    confidence: float
    edited: bool
    bbox: dict


class JobRead(BaseModel):
    id: str
    templateVersionId: str
    templateName: str
    imageUrl: str
    status: str
    results: list[FieldResultRead]
    createdAt: str


@router.post("/preprocess")
async def preprocess(image: UploadFile, session: Session = Depends(get_session)):
    await asyncio.sleep(1.5)
    return ocr_service.preprocess(session)


@router.post("/extract")
async def extract(
    image: UploadFile,
    template_version_id: str = Form(..., alias="templateVersionId"),
    session: Session = Depends(get_session),
):
    ext = os.path.splitext(image.filename or "img.png")[1]
    content = await image.read()

    # Mock delay stays in router
    await asyncio.sleep(2.0)

    result = ocr_service.extract(session, template_version_id, content, ext)
    if not result:
        raise HTTPException(status_code=404, detail="Template version not found")
    return result


MAX_BUNDLE_FILES = 20

@router.post("/extract-bundle")
async def extract_bundle(
    images: list[UploadFile],
    bundle_id: str = Form(..., alias="bundleId"),
    session: Session = Depends(get_session),
):
    if len(images) > MAX_BUNDLE_FILES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_BUNDLE_FILES} files allowed")

    files = []
    for img in images:
        ext = os.path.splitext(img.filename or "img.png")[1]
        content = await img.read()
        files.append((content, ext))

    await asyncio.sleep(0.5 * len(images))

    try:
        result = ocr_service.extract_bundle(session, bundle_id, files)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return result


@router.get("/jobs/bundle/{bundle_id}", response_model=list[JobRead])
def get_bundle_jobs(bundle_id: str, session: Session = Depends(get_session)):
    return ocr_service.list_bundle_jobs(session, bundle_id)


@router.get("/jobs", response_model=list[JobRead])
def list_jobs(session: Session = Depends(get_session)):
    return ocr_service.list_jobs(session)


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: str, session: Session = Depends(get_session)):
    result = ocr_service.get_job(session, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.patch("/jobs/{job_id}/fields/{field_id}")
def update_field_value(
    job_id: str, field_id: str, body: FieldValueUpdate,
    session: Session = Depends(get_session),
):
    result = ocr_service.update_field_value(session, job_id, field_id, body.value)
    if not result:
        raise HTTPException(status_code=404, detail="Field result not found")
    return result


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: str, session: Session = Depends(get_session)):
    if not ocr_service.delete_job(session, job_id):
        raise HTTPException(status_code=404, detail="Job not found")
