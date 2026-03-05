import os
import uuid

from sqlmodel import Session, select

from app.models.ocr import OcrJob, OcrFieldResult
from app.models.template import Template, TemplateVersion
from app.services.ocr_mock import mock_preprocess, mock_extract
from app.services import bundle_service

UPLOADS_DIR = "uploads"


def build_image_url(image_path: str) -> str:
    if not image_path:
        return ""
    return f"/api/images/{os.path.basename(image_path)}"


def build_field_result_read(r: OcrFieldResult) -> dict:
    return {
        "id": r.id, "fieldId": r.field_id, "fieldName": r.field_name,
        "value": r.value, "confidence": r.confidence, "edited": r.edited,
        "bbox": {"x": r.x, "y": r.y, "w": r.w, "h": r.h},
    }


def build_job_read(job: OcrJob, results: list[OcrFieldResult]) -> dict:
    return {
        "id": job.id, "templateVersionId": job.template_version_id,
        "templateName": job.template_name, "imageUrl": build_image_url(job.image_path),
        "status": job.status, "results": [build_field_result_read(r) for r in results],
        "createdAt": job.created_at.isoformat(),
    }


def preprocess(session: Session) -> dict:
    return mock_preprocess(session)


def _create_job(
    session: Session, template_version_id: str,
    image_content: bytes, image_ext: str,
    bundle_id: str | None = None,
) -> tuple[OcrJob, list[OcrFieldResult]] | None:
    """Create OcrJob + results without committing. Returns (job, results) or None."""
    version = session.get(TemplateVersion, template_version_id)
    if not version:
        return None

    filename = f"{uuid.uuid4()}{image_ext}"
    filepath = os.path.join(UPLOADS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_content)

    template = session.get(Template, version.template_id)
    template_name = template.name if template else "Unknown"

    job = OcrJob(
        template_version_id=template_version_id,
        template_name=template_name,
        image_path=filepath, status="processing",
        bundle_id=bundle_id,
    )
    session.add(job)
    session.flush()

    mock_results = mock_extract(session, template_version_id)
    db_results = []
    for mr in mock_results:
        result = OcrFieldResult(
            job_id=job.id, field_id=mr["fieldId"], field_name=mr["fieldName"],
            value=mr["value"], confidence=mr["confidence"],
            x=mr["x"], y=mr["y"], w=mr["w"], h=mr["h"],
        )
        session.add(result)
        db_results.append(result)

    job.status = "done"
    session.add(job)
    return job, db_results


def extract(session: Session, template_version_id: str, image_content: bytes, image_ext: str) -> dict | None:
    result = _create_job(session, template_version_id, image_content, image_ext)
    if not result:
        return None
    job, db_results = result
    session.commit()
    session.refresh(job)
    return build_job_read(job, db_results)


def list_jobs(session: Session) -> list[dict]:
    stmt = select(OcrJob).where(
        OcrJob.bundle_id == None  # noqa: E711 - SQLAlchemy IS NULL
    ).order_by(OcrJob.created_at.desc())  # type: ignore[attr-defined]
    jobs = session.exec(stmt).all()
    result = []
    for job in jobs:
        results_stmt = select(OcrFieldResult).where(OcrFieldResult.job_id == job.id)
        results = list(session.exec(results_stmt).all())
        result.append(build_job_read(job, results))
    return result


def get_job(session: Session, job_id: str) -> dict | None:
    job = session.get(OcrJob, job_id)
    if not job:
        return None
    results_stmt = select(OcrFieldResult).where(OcrFieldResult.job_id == job_id)
    results = list(session.exec(results_stmt).all())
    return build_job_read(job, results)


def update_field_value(session: Session, job_id: str, field_id: str, value: str) -> dict | None:
    stmt = select(OcrFieldResult).where(
        OcrFieldResult.job_id == job_id,
        OcrFieldResult.field_id == field_id,
    )
    result = session.exec(stmt).first()
    if not result:
        return None

    result.value = value
    result.edited = True
    session.add(result)
    session.commit()
    session.refresh(result)
    return build_field_result_read(result)


def extract_bundle(
    session: Session, bundle_id: str,
    files: list[tuple[bytes, str]],
) -> list[dict] | None:
    bundle_data = bundle_service.get_bundle(session, bundle_id)
    if not bundle_data:
        return None

    items = bundle_data["items"]
    if len(files) != len(items):
        raise ValueError(f"Expected {len(items)} files, got {len(files)}")

    # Validate all items have active versions before processing
    for item in items:
        if not item.get("activeVersionId"):
            raise ValueError(f"Template '{item['templateName']}' has no active version")

    # Create all jobs in a single transaction (no commit until all succeed)
    job_pairs: list[tuple[OcrJob, list[OcrFieldResult]]] = []
    for (content, ext), item in zip(files, items):
        result = _create_job(session, item["activeVersionId"], content, ext, bundle_id=bundle_id)
        if not result:
            session.rollback()
            raise ValueError(f"Failed to process file for template '{item['templateName']}'")
        job_pairs.append(result)

    # Commit all at once - atomic
    session.commit()

    results = []
    for job, db_results in job_pairs:
        session.refresh(job)
        results.append(build_job_read(job, db_results))
    return results


def list_bundle_jobs(session: Session, bundle_id: str) -> list[dict]:
    stmt = select(OcrJob).where(
        OcrJob.bundle_id == bundle_id
    ).order_by(OcrJob.created_at)  # type: ignore[attr-defined]
    jobs = session.exec(stmt).all()
    result = []
    for job in jobs:
        results_stmt = select(OcrFieldResult).where(OcrFieldResult.job_id == job.id)
        field_results = list(session.exec(results_stmt).all())
        result.append(build_job_read(job, field_results))
    return result


def delete_job(session: Session, job_id: str) -> bool:
    job = session.get(OcrJob, job_id)
    if not job:
        return False

    results_stmt = select(OcrFieldResult).where(OcrFieldResult.job_id == job_id)
    for r in session.exec(results_stmt).all():
        session.delete(r)

    if job.image_path and os.path.isfile(job.image_path):
        os.remove(job.image_path)

    session.delete(job)
    session.commit()
    return True
