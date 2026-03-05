import json
import os
import uuid

from sqlmodel import Session, select, func

from app.models.template import Template, TemplateVersion, TemplateField

UPLOADS_DIR = "uploads"


def build_image_url(image_path: str) -> str:
    if not image_path:
        return ""
    return f"/api/images/{os.path.basename(image_path)}"


def build_field_read(f: TemplateField) -> dict:
    return {
        "id": f.id, "name": f.name, "color": f.color,
        "bbox": {"x": f.x, "y": f.y, "w": f.w, "h": f.h},
    }


def build_version_read(v: TemplateVersion, fields: list[TemplateField]) -> dict:
    return {
        "id": v.id, "templateId": v.template_id, "version": v.version,
        "status": v.status, "imageUrl": build_image_url(v.image_path),
        "fields": [build_field_read(f) for f in fields],
        "createdAt": v.created_at.isoformat(),
    }


def list_templates(session: Session) -> list[dict]:
    stmt = select(Template).order_by(Template.created_at.desc())  # type: ignore[attr-defined]
    templates = session.exec(stmt).all()
    result = []
    for t in templates:
        count_stmt = select(func.count()).where(TemplateVersion.template_id == t.id)
        version_count = session.exec(count_stmt).one()
        result.append({
            "id": t.id, "name": t.name, "description": t.description,
            "activeVersionId": t.active_version_id, "versionCount": version_count,
            "createdAt": t.created_at.isoformat(),
        })
    return result


def create_template(session: Session, name: str, description: str | None) -> dict:
    template = Template(name=name, description=description)
    session.add(template)
    session.commit()
    session.refresh(template)
    return {
        "id": template.id, "name": template.name, "description": template.description,
        "activeVersionId": template.active_version_id, "createdAt": template.created_at.isoformat(),
    }


def get_template(session: Session, template_id: str) -> dict | None:
    template = session.get(Template, template_id)
    if not template:
        return None

    versions_stmt = select(TemplateVersion).where(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.created_at.desc())  # type: ignore[attr-defined]
    versions = session.exec(versions_stmt).all()

    version_reads = []
    for v in versions:
        fields_stmt = select(TemplateField).where(TemplateField.version_id == v.id)
        fields = list(session.exec(fields_stmt).all())
        version_reads.append(build_version_read(v, fields))

    return {
        "id": template.id, "name": template.name, "description": template.description,
        "activeVersionId": template.active_version_id, "versions": version_reads,
        "createdAt": template.created_at.isoformat(),
    }


def update_template(session: Session, template_id: str, name: str | None, description: str | None) -> dict | None:
    template = session.get(Template, template_id)
    if not template:
        return None
    if name is not None:
        template.name = name
    if description is not None:
        template.description = description
    session.add(template)
    session.commit()
    session.refresh(template)
    return {
        "id": template.id, "name": template.name, "description": template.description,
        "activeVersionId": template.active_version_id, "createdAt": template.created_at.isoformat(),
    }


def delete_template(session: Session, template_id: str) -> bool:
    template = session.get(Template, template_id)
    if not template:
        return False

    versions_stmt = select(TemplateVersion).where(TemplateVersion.template_id == template_id)
    versions = session.exec(versions_stmt).all()
    for v in versions:
        fields_stmt = select(TemplateField).where(TemplateField.version_id == v.id)
        for f in session.exec(fields_stmt).all():
            session.delete(f)
        if v.image_path and os.path.isfile(v.image_path):
            os.remove(v.image_path)
        session.delete(v)

    session.delete(template)
    session.commit()
    return True


def list_versions(session: Session, template_id: str) -> list[dict]:
    stmt = select(TemplateVersion).where(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.created_at.desc())  # type: ignore[attr-defined]
    versions = session.exec(stmt).all()
    result = []
    for v in versions:
        fields_stmt = select(TemplateField).where(TemplateField.version_id == v.id)
        fields = list(session.exec(fields_stmt).all())
        result.append(build_version_read(v, fields))
    return result


def create_version(
    session: Session, template_id: str, version: str,
    image_content: bytes, image_ext: str, fields_data: str,
) -> dict | None:
    template = session.get(Template, template_id)
    if not template:
        return None

    # Save image
    filename = f"{uuid.uuid4()}{image_ext}"
    filepath = os.path.join(UPLOADS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_content)

    # Deactivate siblings
    siblings_stmt = select(TemplateVersion).where(TemplateVersion.template_id == template_id)
    for sib in session.exec(siblings_stmt).all():
        sib.status = "inactive"
        session.add(sib)

    # Create version
    new_version = TemplateVersion(
        template_id=template_id, version=version,
        status="active", image_path=filepath,
    )
    session.add(new_version)
    session.flush()

    # Create fields
    parsed_fields = json.loads(fields_data)
    db_fields = []
    for fd in parsed_fields:
        bbox = fd.get("bbox", {})
        tf = TemplateField(
            version_id=new_version.id, name=fd.get("name", ""),
            color=fd.get("color", "#2196F3"),
            x=bbox.get("x", 0), y=bbox.get("y", 0),
            w=bbox.get("w", 0), h=bbox.get("h", 0),
        )
        session.add(tf)
        db_fields.append(tf)

    # Update template active version
    template.active_version_id = new_version.id
    session.add(template)
    session.commit()
    session.refresh(new_version)

    return build_version_read(new_version, db_fields)


def suggest_version(session: Session, template_id: str) -> dict:
    count_stmt = select(func.count()).where(TemplateVersion.template_id == template_id)
    count = session.exec(count_stmt).one()
    return {"version": f"v{count + 1}"}


def activate_version(session: Session, version_id: str) -> dict | None:
    version = session.get(TemplateVersion, version_id)
    if not version:
        return None

    # Deactivate siblings
    siblings_stmt = select(TemplateVersion).where(TemplateVersion.template_id == version.template_id)
    for sib in session.exec(siblings_stmt).all():
        sib.status = "inactive"
        session.add(sib)

    version.status = "active"
    session.add(version)

    # Update template
    template = session.get(Template, version.template_id)
    if template:
        template.active_version_id = version_id
        session.add(template)

    session.commit()

    fields_stmt = select(TemplateField).where(TemplateField.version_id == version_id)
    fields = list(session.exec(fields_stmt).all())
    return build_version_read(version, fields)


def update_fields(session: Session, version_id: str, fields_data: list[dict]) -> dict | None:
    version = session.get(TemplateVersion, version_id)
    if not version:
        return None

    # Delete existing fields
    old_stmt = select(TemplateField).where(TemplateField.version_id == version_id)
    for old_f in session.exec(old_stmt).all():
        session.delete(old_f)

    # Insert new fields
    new_fields = []
    for fd in fields_data:
        bbox = fd.get("bbox", {})
        tf = TemplateField(
            version_id=version_id, name=fd.get("name", ""),
            color=fd.get("color", "#2196F3"),
            x=bbox.get("x", 0), y=bbox.get("y", 0),
            w=bbox.get("w", 0), h=bbox.get("h", 0),
        )
        session.add(tf)
        new_fields.append(tf)

    session.commit()
    session.refresh(version)
    return build_version_read(version, new_fields)
