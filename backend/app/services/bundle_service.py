from sqlmodel import Session, select, func

from app.models.bundle import Bundle, BundleItem
from app.models.template import Template


def list_bundles(session: Session) -> list[dict]:
    stmt = select(Bundle).order_by(Bundle.created_at.desc())  # type: ignore[attr-defined]
    bundles = session.exec(stmt).all()
    result = []
    for b in bundles:
        count_stmt = select(func.count()).where(BundleItem.bundle_id == b.id)
        count = session.exec(count_stmt).one()
        result.append({
            "id": b.id, "name": b.name, "description": b.description,
            "templateCount": count, "createdAt": b.created_at.isoformat(),
        })
    return result


def create_bundle(session: Session, name: str, description: str | None, template_ids: list[str]) -> dict:
    # Validate template_ids - raises ValueError if invalid
    for tid in template_ids:
        if not session.get(Template, tid):
            raise ValueError(f"Template {tid} not found")

    bundle = Bundle(name=name, description=description)
    session.add(bundle)
    session.flush()

    for i, tid in enumerate(template_ids):
        item = BundleItem(bundle_id=bundle.id, template_id=tid, sort_order=i)
        session.add(item)

    session.commit()
    session.refresh(bundle)
    return {
        "id": bundle.id, "name": bundle.name, "description": bundle.description,
        "templateCount": len(template_ids), "createdAt": bundle.created_at.isoformat(),
    }


def get_bundle(session: Session, bundle_id: str) -> dict | None:
    bundle = session.get(Bundle, bundle_id)
    if not bundle:
        return None

    items_stmt = select(BundleItem).where(
        BundleItem.bundle_id == bundle_id
    ).order_by(BundleItem.sort_order)  # type: ignore[attr-defined]
    items = session.exec(items_stmt).all()

    item_reads = []
    for item in items:
        tmpl = session.get(Template, item.template_id)
        item_reads.append({
            "id": item.id, "templateId": item.template_id,
            "templateName": tmpl.name if tmpl else "Unknown",
            "activeVersionId": tmpl.active_version_id if tmpl else None,
            "sortOrder": item.sort_order,
        })

    return {
        "id": bundle.id, "name": bundle.name, "description": bundle.description,
        "templateCount": len(item_reads), "items": item_reads,
        "createdAt": bundle.created_at.isoformat(),
    }


def update_bundle(
    session: Session, bundle_id: str,
    name: str | None, description: str | None, template_ids: list[str] | None,
) -> dict | None:
    bundle = session.get(Bundle, bundle_id)
    if not bundle:
        return None

    if name is not None:
        bundle.name = name
    if description is not None:
        bundle.description = description
    session.add(bundle)

    if template_ids is not None:
        for tid in template_ids:
            if not session.get(Template, tid):
                raise ValueError(f"Template {tid} not found")
        # Delete old items
        old_stmt = select(BundleItem).where(BundleItem.bundle_id == bundle_id)
        for old in session.exec(old_stmt).all():
            session.delete(old)
        # Create new
        for i, tid in enumerate(template_ids):
            session.add(BundleItem(bundle_id=bundle_id, template_id=tid, sort_order=i))

    session.commit()
    session.refresh(bundle)

    count_stmt = select(func.count()).where(BundleItem.bundle_id == bundle_id)
    count = session.exec(count_stmt).one()
    return {
        "id": bundle.id, "name": bundle.name, "description": bundle.description,
        "templateCount": count, "createdAt": bundle.created_at.isoformat(),
    }


def delete_bundle(session: Session, bundle_id: str) -> bool:
    bundle = session.get(Bundle, bundle_id)
    if not bundle:
        return False

    items_stmt = select(BundleItem).where(BundleItem.bundle_id == bundle_id)
    for item in session.exec(items_stmt).all():
        session.delete(item)

    session.delete(bundle)
    session.commit()
    return True
