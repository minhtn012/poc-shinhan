import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app as fastapi_app


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session, tmp_path):
    """Create a test client with mocked dependencies."""

    def get_session_override():
        return session

    # Mock uploads directory
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(exist_ok=True)

    # Patch the UPLOADS_DIR in services and images router
    import app.services.template_service
    import app.services.ocr_service
    import app.routers.images
    original_templates_dir = app.services.template_service.UPLOADS_DIR
    original_ocr_dir = app.services.ocr_service.UPLOADS_DIR
    original_images_dir = app.routers.images.UPLOADS_DIR

    app.services.template_service.UPLOADS_DIR = str(uploads_dir)
    app.services.ocr_service.UPLOADS_DIR = str(uploads_dir)
    app.routers.images.UPLOADS_DIR = str(uploads_dir)

    fastapi_app.dependency_overrides[get_session] = get_session_override

    client = TestClient(fastapi_app)

    yield client

    # Cleanup
    fastapi_app.dependency_overrides.clear()
    app.services.template_service.UPLOADS_DIR = original_templates_dir
    app.services.ocr_service.UPLOADS_DIR = original_ocr_dir
    app.routers.images.UPLOADS_DIR = original_images_dir

    # Clean up uploaded files
    if uploads_dir.exists():
        shutil.rmtree(uploads_dir, ignore_errors=True)


@pytest.fixture
def sample_image_bytes():
    """Create minimal sample PNG image bytes (1x1 transparent PNG)."""
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
