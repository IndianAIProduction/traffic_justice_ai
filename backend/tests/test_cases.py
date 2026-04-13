import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_case(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/cases",
        json={
            "case_type": "challan",
            "title": "Overcharged challan on highway",
            "state": "Maharashtra",
            "city": "Mumbai",
            "description": "Was charged Rs 15000 for dangerous driving",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Overcharged challan on highway"
    assert data["case_type"] == "challan"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_list_cases(client: AsyncClient, auth_headers):
    # Create a case first
    await client.post(
        "/api/v1/cases",
        json={"case_type": "traffic_stop", "title": "Routine stop"},
        headers=auth_headers,
    )
    response = await client.get("/api/v1/cases", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_case_detail(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/cases",
        json={"case_type": "misconduct", "title": "Officer misconduct report"},
        headers=auth_headers,
    )
    case_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/cases/{case_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case_id
    assert data["title"] == "Officer misconduct report"


@pytest.mark.asyncio
async def test_update_case(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/cases",
        json={"case_type": "challan", "title": "Test case"},
        headers=auth_headers,
    )
    case_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "in_progress", "description": "Updated description"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert response.json()["description"] == "Updated description"


@pytest.mark.asyncio
async def test_case_not_found(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/cases/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404
