import random

from sqlmodel import Session, select

from app.models.template import Template, TemplateVersion, TemplateField

SAMPLE_VALUES = {
    "name": "Nguyen Van A",
    "date": "2026-01-15",
    "amount": "15,000,000",
    "account": "1234-5678-9012",
    "id_number": "079012345678",
    "address": "123 Le Loi, Q1, HCM",
}


def mock_preprocess(session: Session) -> dict | None:
    """Find first template with an active version."""
    stmt = select(Template).where(Template.active_version_id.is_not(None))  # type: ignore[union-attr]
    template = session.exec(stmt).first()
    if not template:
        return None
    return {
        "templateId": template.id,
        "templateName": template.name,
        "confidence": 0.92,
    }


def mock_extract(session: Session, version_id: str) -> list[dict]:
    """Generate fake OCR results from version fields."""
    version = session.get(TemplateVersion, version_id)
    if not version:
        return []

    fields_stmt = select(TemplateField).where(TemplateField.version_id == version_id)
    fields = session.exec(fields_stmt).all()

    results = []
    for field in fields:
        value = SAMPLE_VALUES.get(field.name.lower(), f"Sample {field.name}")
        results.append({
            "fieldId": field.id,
            "fieldName": field.name,
            "value": value,
            "confidence": round(0.75 + random.random() * 0.2, 4),
            "x": field.x,
            "y": field.y,
            "w": field.w,
            "h": field.h,
        })
    return results
