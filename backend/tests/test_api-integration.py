"""
Comprehensive API Integration Tests for OCR Backend.
Tests real API calls without mocking - CRUD flow: create → read → update → delete.
"""
import io
import json

import pytest


class TestTemplateAPI:
    """Test Template endpoints: create, list, get, update, delete."""

    def test_create_template(self, client, session):
        """Test creating a template."""
        response = client.post(
            "/api/templates",
            json={
                "name": "Test Invoice Template",
                "description": "Invoice processing template"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Invoice Template"
        assert data["description"] == "Invoice processing template"
        assert "id" in data
        assert "createdAt" in data
        assert data["activeVersionId"] is None
        return data["id"]

    def test_create_template_without_description(self, client):
        """Test creating template without optional description."""
        response = client.post(
            "/api/templates",
            json={"name": "Simple Template"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Template"
        assert data["description"] is None

    def test_list_templates_empty(self, client):
        """Test listing templates when DB is empty."""
        response = client.get("/api/templates")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_templates_after_creation(self, client):
        """Test listing templates after creating some."""
        # Create 3 templates
        ids = []
        for i in range(3):
            resp = client.post(
                "/api/templates",
                json={
                    "name": f"Template {i}",
                    "description": f"Description {i}"
                }
            )
            assert resp.status_code == 201
            ids.append(resp.json()["id"])

        # List all
        response = client.get("/api/templates")
        assert response.status_code == 200
        templates = response.json()
        assert len(templates) == 3
        # Most recent first
        assert templates[0]["name"] == "Template 2"
        assert templates[1]["name"] == "Template 1"
        assert templates[2]["name"] == "Template 0"

    def test_get_template(self, client):
        """Test getting a single template by ID."""
        # Create
        create_resp = client.post(
            "/api/templates",
            json={"name": "Get Test", "description": "Test description"}
        )
        template_id = create_resp.json()["id"]

        # Get
        response = client.get(f"/api/templates/{template_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == "Get Test"
        assert data["description"] == "Test description"
        assert data["versions"] == []
        assert data["activeVersionId"] is None

    def test_get_template_not_found(self, client):
        """Test getting non-existent template."""
        response = client.get("/api/templates/nonexistent-id")
        assert response.status_code == 404
        assert "Template not found" in response.json()["detail"]

    def test_update_template(self, client):
        """Test updating template name and description."""
        # Create
        create_resp = client.post(
            "/api/templates",
            json={"name": "Original", "description": "Original desc"}
        )
        template_id = create_resp.json()["id"]

        # Update
        response = client.put(
            f"/api/templates/{template_id}",
            json={"name": "Updated", "description": "Updated desc"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "Updated desc"

        # Verify persistence
        get_resp = client.get(f"/api/templates/{template_id}")
        assert get_resp.json()["name"] == "Updated"

    def test_update_template_partial(self, client):
        """Test partial update (only name or only description)."""
        create_resp = client.post(
            "/api/templates",
            json={"name": "Original", "description": "Original desc"}
        )
        template_id = create_resp.json()["id"]

        # Update only name
        response = client.put(
            f"/api/templates/{template_id}",
            json={"name": "New Name"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"
        assert response.json()["description"] == "Original desc"

    def test_update_template_not_found(self, client):
        """Test updating non-existent template."""
        response = client.put(
            "/api/templates/nonexistent",
            json={"name": "New"}
        )
        assert response.status_code == 404

    def test_delete_template(self, client):
        """Test deleting a template."""
        create_resp = client.post(
            "/api/templates",
            json={"name": "To Delete"}
        )
        template_id = create_resp.json()["id"]

        # Delete
        response = client.delete(f"/api/templates/{template_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(f"/api/templates/{template_id}")
        assert get_resp.status_code == 404

    def test_delete_template_not_found(self, client):
        """Test deleting non-existent template."""
        response = client.delete("/api/templates/nonexistent")
        assert response.status_code == 404


class TestTemplateVersionAPI:
    """Test Template Version endpoints: create, list, activate, update fields."""

    def test_create_version(self, client, sample_image_bytes):
        """Test creating a template version with image and fields."""
        # Create template
        template_resp = client.post(
            "/api/templates",
            json={"name": "Invoice Template"}
        )
        template_id = template_resp.json()["id"]

        # Create version
        fields = [
            {"name": "Invoice Number", "color": "#FF5252", "bbox": {"x": 10, "y": 20, "w": 100, "h": 30}},
            {"name": "Date", "color": "#2196F3", "bbox": {"x": 150, "y": 20, "w": 100, "h": 30}},
        ]
        response = client.post(
            f"/api/templates/{template_id}/versions",
            data={"version": "v1", "fields": json.dumps(fields)},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["version"] == "v1"
        assert data["status"] == "active"
        assert data["templateId"] == template_id
        assert len(data["fields"]) == 2
        assert data["fields"][0]["name"] == "Invoice Number"
        assert data["fields"][1]["name"] == "Date"
        assert "imageUrl" in data
        return template_id, data["id"]

    def test_create_version_without_fields(self, client, sample_image_bytes):
        """Test creating version without fields."""
        template_resp = client.post(
            "/api/templates",
            json={"name": "Template"}
        )
        template_id = template_resp.json()["id"]

        response = client.post(
            f"/api/templates/{template_id}/versions",
            data={"version": "v1"},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["fields"] == []

    def test_create_version_on_nonexistent_template(self, client, sample_image_bytes):
        """Test creating version on non-existent template."""
        response = client.post(
            "/api/templates/nonexistent/versions",
            data={"version": "v1"},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        assert response.status_code == 404

    def test_list_versions(self, client, sample_image_bytes):
        """Test listing versions of a template."""
        template_id, _ = self.test_create_version(client, sample_image_bytes)

        # Create another version
        fields = [{"name": "Field", "color": "#2196F3", "bbox": {"x": 0, "y": 0, "w": 100, "h": 50}}]
        client.post(
            f"/api/templates/{template_id}/versions",
            data={"version": "v2", "fields": json.dumps(fields)},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        )

        # List
        response = client.get(f"/api/templates/{template_id}/versions")
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 2
        assert versions[0]["version"] == "v2"  # Most recent first
        assert versions[1]["version"] == "v1"

    def test_suggest_version(self, client, sample_image_bytes):
        """Test version suggestion."""
        template_id, _ = self.test_create_version(client, sample_image_bytes)

        response = client.get(f"/api/templates/{template_id}/suggest-version")
        assert response.status_code == 200
        assert response.json()["version"] == "v2"

    def test_activate_version(self, client, sample_image_bytes):
        """Test activating a version."""
        template_id, version1_id = self.test_create_version(client, sample_image_bytes)

        # Create v2 (will become active)
        fields = [{"name": "Field", "color": "#2196F3", "bbox": {"x": 0, "y": 0, "w": 100, "h": 50}}]
        v2_resp = client.post(
            f"/api/templates/{template_id}/versions",
            data={"version": "v2", "fields": json.dumps(fields)},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        version2_id = v2_resp.json()["id"]

        # Activate v1
        response = client.put(f"/api/versions/{version1_id}/activate")
        assert response.status_code == 200
        assert response.json()["status"] == "active"

        # Verify v2 is now inactive
        v2_get = client.get(f"/api/templates/{template_id}/versions")
        versions = v2_get.json()
        v1 = next((v for v in versions if v["id"] == version1_id), None)
        v2 = next((v for v in versions if v["id"] == version2_id), None)
        assert v1["status"] == "active"
        assert v2["status"] == "inactive"

    def test_activate_nonexistent_version(self, client):
        """Test activating non-existent version."""
        response = client.put("/api/versions/nonexistent/activate")
        assert response.status_code == 404

    def test_update_version_fields(self, client, sample_image_bytes):
        """Test updating fields of a version."""
        template_id, version_id = self.test_create_version(client, sample_image_bytes)

        # Update fields
        new_fields = [
            {"name": "Updated Field 1", "color": "#4CAF50", "bbox": {"x": 0, "y": 0, "w": 50, "h": 50}},
            {"name": "Updated Field 2", "color": "#FF9800", "bbox": {"x": 60, "y": 0, "w": 50, "h": 50}},
            {"name": "Updated Field 3", "color": "#9C27B0", "bbox": {"x": 120, "y": 0, "w": 50, "h": 50}},
        ]
        response = client.put(
            f"/api/versions/{version_id}/fields",
            json={"fields": new_fields}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["fields"]) == 3
        assert data["fields"][0]["name"] == "Updated Field 1"
        assert data["fields"][1]["color"] == "#FF9800"

        # Verify persistence
        get_resp = client.get(f"/api/templates/{template_id}/versions")
        version = next((v for v in get_resp.json() if v["id"] == version_id))
        assert len(version["fields"]) == 3

    def test_update_fields_nonexistent_version(self, client):
        """Test updating fields on non-existent version."""
        response = client.put(
            "/api/versions/nonexistent/fields",
            json={"fields": []}
        )
        assert response.status_code == 404


class TestBundleAPI:
    """Test Bundle endpoints: create, list, get, update, delete."""

    def _create_test_template(self, client):
        """Helper to create a template."""
        resp = client.post(
            "/api/templates",
            json={"name": "Bundle Template"}
        )
        return resp.json()["id"]

    def test_create_bundle_empty(self, client):
        """Test creating an empty bundle."""
        response = client.post(
            "/api/bundles",
            json={"name": "Empty Bundle", "description": "No templates"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Empty Bundle"
        assert data["templateCount"] == 0
        return data["id"]

    def test_create_bundle_with_templates(self, client):
        """Test creating bundle with templates."""
        # Create templates
        template_ids = [self._create_test_template(client) for _ in range(3)]

        # Create bundle
        response = client.post(
            "/api/bundles",
            json={
                "name": "Multi-Template Bundle",
                "description": "Contains multiple templates",
                "templateIds": template_ids
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Multi-Template Bundle"
        assert data["templateCount"] == 3
        return data["id"]

    def test_create_bundle_with_invalid_template(self, client):
        """Test creating bundle with non-existent template."""
        response = client.post(
            "/api/bundles",
            json={
                "name": "Invalid Bundle",
                "templateIds": ["nonexistent-id"]
            }
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_list_bundles_empty(self, client):
        """Test listing bundles when none exist."""
        response = client.get("/api/bundles")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_bundles_after_creation(self, client):
        """Test listing bundles after creation."""
        # Create 2 bundles
        ids = []
        for i in range(2):
            resp = client.post(
                "/api/bundles",
                json={"name": f"Bundle {i}", "description": f"Desc {i}"}
            )
            ids.append(resp.json()["id"])

        # List
        response = client.get("/api/bundles")
        assert response.status_code == 200
        bundles = response.json()
        assert len(bundles) == 2
        assert bundles[0]["name"] == "Bundle 1"  # Most recent first
        assert bundles[1]["name"] == "Bundle 0"

    def test_get_bundle(self, client):
        """Test getting a bundle with its items."""
        # Create templates and bundle
        template_ids = [self._create_test_template(client) for _ in range(2)]
        create_resp = client.post(
            "/api/bundles",
            json={"name": "Test Bundle", "templateIds": template_ids}
        )
        bundle_id = create_resp.json()["id"]

        # Get
        response = client.get(f"/api/bundles/{bundle_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bundle_id
        assert data["name"] == "Test Bundle"
        assert data["templateCount"] == 2
        assert len(data["items"]) == 2
        assert all("templateName" in item for item in data["items"])

    def test_get_bundle_not_found(self, client):
        """Test getting non-existent bundle."""
        response = client.get("/api/bundles/nonexistent")
        assert response.status_code == 404

    def test_update_bundle_name(self, client):
        """Test updating bundle name."""
        bundle_id = self.test_create_bundle_empty(client)

        response = client.put(
            f"/api/bundles/{bundle_id}",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

        # Verify persistence
        get_resp = client.get(f"/api/bundles/{bundle_id}")
        assert get_resp.json()["name"] == "Updated Name"

    def test_update_bundle_templates(self, client):
        """Test updating bundle templates."""
        # Create bundle with 1 template
        template1 = self._create_test_template(client)
        create_resp = client.post(
            "/api/bundles",
            json={"name": "Update Test", "templateIds": [template1]}
        )
        bundle_id = create_resp.json()["id"]

        # Add more templates
        template2 = self._create_test_template(client)
        template3 = self._create_test_template(client)

        response = client.put(
            f"/api/bundles/{bundle_id}",
            json={"templateIds": [template1, template2, template3]}
        )
        assert response.status_code == 200
        assert response.json()["templateCount"] == 3

    def test_update_bundle_with_invalid_template(self, client):
        """Test updating bundle with non-existent template."""
        bundle_id = self.test_create_bundle_empty(client)

        response = client.put(
            f"/api/bundles/{bundle_id}",
            json={"templateIds": ["nonexistent"]}
        )
        assert response.status_code == 400

    def test_delete_bundle(self, client):
        """Test deleting a bundle."""
        bundle_id = self.test_create_bundle_empty(client)

        response = client.delete(f"/api/bundles/{bundle_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(f"/api/bundles/{bundle_id}")
        assert get_resp.status_code == 404

    def test_delete_bundle_not_found(self, client):
        """Test deleting non-existent bundle."""
        response = client.delete("/api/bundles/nonexistent")
        assert response.status_code == 404


class TestOCRAPI:
    """Test OCR Job endpoints: extract, list, get, update field, delete."""

    def _create_template_version(self, client, sample_image_bytes):
        """Helper to create a template with a version."""
        template_resp = client.post(
            "/api/templates",
            json={"name": "OCR Template"}
        )
        template_id = template_resp.json()["id"]

        fields = [
            {"name": "Extracted Text", "color": "#2196F3", "bbox": {"x": 0, "y": 0, "w": 100, "h": 50}},
        ]
        version_resp = client.post(
            f"/api/templates/{template_id}/versions",
            data={"version": "v1", "fields": json.dumps(fields)},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        return template_id, version_resp.json()["id"]

    def test_extract_creates_job(self, client, sample_image_bytes):
        """Test OCR extraction creates job with results."""
        _, version_id = self._create_template_version(client, sample_image_bytes)

        # Extract
        response = client.post(
            "/api/ocr/extract",
            data={"templateVersionId": version_id},
            files={"image": ("doc.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["templateVersionId"] == version_id
        assert data["status"] == "done"
        assert "id" in data
        assert "imageUrl" in data
        assert len(data["results"]) > 0
        return data["id"]

    def test_extract_with_invalid_version(self, client, sample_image_bytes):
        """Test extracting with non-existent template version."""
        response = client.post(
            "/api/ocr/extract",
            data={"templateVersionId": "nonexistent"},
            files={"image": ("doc.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        assert response.status_code == 404

    def test_list_jobs_empty(self, client):
        """Test listing jobs when none exist."""
        response = client.get("/api/ocr/jobs")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_jobs_after_extraction(self, client, sample_image_bytes):
        """Test listing jobs after creating some."""
        _, version_id = self._create_template_version(client, sample_image_bytes)

        # Create 2 jobs
        for _ in range(2):
            client.post(
                "/api/ocr/extract",
                data={"templateVersionId": version_id},
                files={"image": ("doc.png", io.BytesIO(sample_image_bytes), "image/png")}
            )

        # List
        response = client.get("/api/ocr/jobs")
        assert response.status_code == 200
        jobs = response.json()
        assert len(jobs) == 2
        assert all(job["status"] == "done" for job in jobs)

    def test_get_job(self, client, sample_image_bytes):
        """Test getting a single job."""
        job_id = self.test_extract_creates_job(client, sample_image_bytes)

        response = client.get(f"/api/ocr/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["status"] == "done"
        assert "results" in data
        assert len(data["results"]) > 0

    def test_get_job_not_found(self, client):
        """Test getting non-existent job."""
        response = client.get("/api/ocr/jobs/nonexistent")
        assert response.status_code == 404

    def test_update_field_value(self, client, sample_image_bytes):
        """Test updating an OCR field value."""
        job_id = self.test_extract_creates_job(client, sample_image_bytes)

        # Get job to find field IDs
        job_resp = client.get(f"/api/ocr/jobs/{job_id}")
        job_data = job_resp.json()
        field_id = job_data["results"][0]["fieldId"]

        # Update field
        response = client.patch(
            f"/api/ocr/jobs/{job_id}/fields/{field_id}",
            json={"value": "Updated Value"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "Updated Value"
        assert data["edited"] is True

        # Verify persistence
        job_resp = client.get(f"/api/ocr/jobs/{job_id}")
        updated_field = next(
            (f for f in job_resp.json()["results"] if f["fieldId"] == field_id),
            None
        )
        assert updated_field["value"] == "Updated Value"
        assert updated_field["edited"] is True

    def test_update_field_nonexistent_field(self, client, sample_image_bytes):
        """Test updating non-existent field."""
        job_id = self.test_extract_creates_job(client, sample_image_bytes)

        response = client.patch(
            f"/api/ocr/jobs/{job_id}/fields/nonexistent",
            json={"value": "Test"}
        )
        assert response.status_code == 404

    def test_delete_job(self, client, sample_image_bytes):
        """Test deleting a job."""
        job_id = self.test_extract_creates_job(client, sample_image_bytes)

        response = client.delete(f"/api/ocr/jobs/{job_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(f"/api/ocr/jobs/{job_id}")
        assert get_resp.status_code == 404

    def test_delete_job_not_found(self, client):
        """Test deleting non-existent job."""
        response = client.delete("/api/ocr/jobs/nonexistent")
        assert response.status_code == 404


class TestImagesAPI:
    """Test Images endpoint: retrieve uploaded images."""

    def test_get_image_not_found(self, client):
        """Test getting non-existent image."""
        response = client.get("/api/images/nonexistent.png")
        assert response.status_code == 404

    def test_get_image_after_upload(self, client, sample_image_bytes):
        """Test retrieving image after upload via template version."""
        # Create template version (which uploads image)
        template_resp = client.post(
            "/api/templates",
            json={"name": "Image Test Template"}
        )
        template_id = template_resp.json()["id"]

        version_resp = client.post(
            f"/api/templates/{template_id}/versions",
            data={"version": "v1"},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        image_url = version_resp.json()["imageUrl"]

        # Extract filename from URL
        filename = image_url.split("/")[-1]

        # Get image
        response = client.get(f"/api/images/{filename}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")


class TestHealthAPI:
    """Test basic health check."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestCRUDFlowIntegration:
    """Integration tests for complete CRUD flows."""

    def test_full_template_workflow(self, client, sample_image_bytes):
        """Test complete template workflow: create → version → activate → update → delete."""
        # CREATE
        create_resp = client.post(
            "/api/templates",
            json={"name": "Full Workflow", "description": "Test template"}
        )
        assert create_resp.status_code == 201
        template_id = create_resp.json()["id"]

        # LIST - verify creation
        list_resp = client.get("/api/templates")
        assert any(t["id"] == template_id for t in list_resp.json())

        # CREATE VERSION
        fields = [
            {"name": "Field 1", "color": "#FF5252", "bbox": {"x": 0, "y": 0, "w": 100, "h": 50}},
        ]
        version_resp = client.post(
            f"/api/templates/{template_id}/versions",
            data={"version": "v1", "fields": json.dumps(fields)},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        assert version_resp.status_code == 201
        version_id = version_resp.json()["id"]

        # GET - verify version
        get_resp = client.get(f"/api/templates/{template_id}")
        assert get_resp.json()["activeVersionId"] == version_id

        # UPDATE FIELDS
        new_fields = [
            {"name": "Updated Field", "color": "#4CAF50", "bbox": {"x": 0, "y": 0, "w": 150, "h": 60}},
        ]
        update_resp = client.put(
            f"/api/versions/{version_id}/fields",
            json={"fields": new_fields}
        )
        assert update_resp.status_code == 200

        # DELETE
        del_resp = client.delete(f"/api/templates/{template_id}")
        assert del_resp.status_code == 204

        # Verify deletion
        get_resp = client.get(f"/api/templates/{template_id}")
        assert get_resp.status_code == 404

    def test_full_bundle_workflow(self, client):
        """Test complete bundle workflow: create → update → delete."""
        # CREATE templates
        template_ids = []
        for i in range(2):
            resp = client.post(
                "/api/templates",
                json={"name": f"Bundle Template {i}"}
            )
            template_ids.append(resp.json()["id"])

        # CREATE bundle
        create_resp = client.post(
            "/api/bundles",
            json={
                "name": "Bundle Workflow",
                "templateIds": [template_ids[0]]
            }
        )
        assert create_resp.status_code == 201
        bundle_id = create_resp.json()["id"]

        # LIST - verify
        list_resp = client.get("/api/bundles")
        assert any(b["id"] == bundle_id for b in list_resp.json())

        # GET - verify
        get_resp = client.get(f"/api/bundles/{bundle_id}")
        assert get_resp.json()["templateCount"] == 1

        # UPDATE - add template
        update_resp = client.put(
            f"/api/bundles/{bundle_id}",
            json={"templateIds": template_ids}
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["templateCount"] == 2

        # DELETE
        del_resp = client.delete(f"/api/bundles/{bundle_id}")
        assert del_resp.status_code == 204

        # Verify
        get_resp = client.get(f"/api/bundles/{bundle_id}")
        assert get_resp.status_code == 404

    def test_full_ocr_workflow(self, client, sample_image_bytes):
        """Test complete OCR workflow: template → extract → update → delete."""
        # CREATE template with version
        template_resp = client.post(
            "/api/templates",
            json={"name": "OCR Workflow"}
        )
        template_id = template_resp.json()["id"]

        fields = [
            {"name": "Text Field", "color": "#2196F3", "bbox": {"x": 0, "y": 0, "w": 100, "h": 50}},
        ]
        version_resp = client.post(
            f"/api/templates/{template_id}/versions",
            data={"version": "v1", "fields": json.dumps(fields)},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        version_id = version_resp.json()["id"]

        # EXTRACT
        extract_resp = client.post(
            "/api/ocr/extract",
            data={"templateVersionId": version_id},
            files={"image": ("doc.png", io.BytesIO(sample_image_bytes), "image/png")}
        )
        assert extract_resp.status_code == 200
        job_id = extract_resp.json()["id"]

        # LIST jobs
        list_resp = client.get("/api/ocr/jobs")
        assert len(list_resp.json()) > 0

        # GET job
        get_resp = client.get(f"/api/ocr/jobs/{job_id}")
        assert get_resp.status_code == 200
        field_id = get_resp.json()["results"][0]["fieldId"]

        # UPDATE field
        update_resp = client.patch(
            f"/api/ocr/jobs/{job_id}/fields/{field_id}",
            json={"value": "Corrected Text"}
        )
        assert update_resp.status_code == 200

        # DELETE job
        del_resp = client.delete(f"/api/ocr/jobs/{job_id}")
        assert del_resp.status_code == 204

        # Verify
        get_resp = client.get(f"/api/ocr/jobs/{job_id}")
        assert get_resp.status_code == 404
