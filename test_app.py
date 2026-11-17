"""
Unit and integration tests for Scholarship Finder Agent Web Application.
"""
import io
import pytest
import pandas as pd
from app import app
import matching_service


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_homepage(client):
    """Verify web application loads correctly."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"ScholarshipFinder" in response.data
    assert b"Profile & Filters" in response.data


def test_dataset_info(client):
    """Verify dataset metadata endpoint."""
    response = client.get("/api/dataset-info")
    assert response.status_code == 200
    data = response.get_json()
    assert "filename" in data
    assert data["total_scholarships"] >= 20
    assert data["countries_count"] >= 5


def test_list_scholarships(client):
    """Verify scholarships listing and filters."""
    response = client.get("/api/scholarships?degree=master")
    assert response.status_code == 200
    data = response.get_json()
    assert "scholarships" in data
    assert len(data["scholarships"]) > 0


def test_recommendation_endpoint(client):
    """Verify profile recommendation matching endpoint."""
    payload = {
        "degree": "master",
        "cgpa": 3.4,
        "cgpa_scale": 4.0,
        "budget_usd": 5000.0,
        "nationality": "Bangladesh",
        "country": "Germany"
    }
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert len(data["results"]) > 0
    names = [r["name"] for r in data["results"]]
    assert any("DAAD" in n for n in names)


def test_global_scholarships_dataset(client):
    """Verify global destinations such as USA, Japan, Australia are in dataset."""
    response = client.get("/api/dataset-info")
    assert response.status_code == 200
    data = response.get_json()
    countries = data["countries"]
    assert "United States" in countries
    assert "Japan" in countries
    assert "Australia" in countries
    assert "Canada" in countries
    assert data["total_scholarships"] >= 35


def test_chat_endpoint(client):
    """Verify AI chat endpoint returns structured replies."""
    payload = {
        "message": "I want a master's in Germany with CGPA 3.4 out of 4 and budget 5000 USD from Bangladesh",
        "session_id": "test-chat-session"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert len(data["reply"]) > 20


def test_matching_degree_filter():
    df = matching_service.load_data("europe_scholarships_matching.csv")
    res = matching_service.recommend(df, "bachelor", 3.5, 4.0, 50000)
    names = [r["name"] for r in res["results"]]
    assert "Chevening Scholarships" not in names


def test_budget_never_exceeded():
    df = matching_service.load_data("europe_scholarships_matching.csv")
    res = matching_service.recommend(df, "master", 3.5, 4.0, 3000)
    assert all(r["out_of_pocket_usd_per_year"] <= 3000 for r in res["results"])


def test_upload_and_reset_dataset(client):
    """Test custom dataset upload via CSV file."""
    csv_content = """scholarship_name,country,funder,degree_levels,coverage_level,est_annual_cost_usd,est_annual_support_usd
Global Tech Fellowship,Japan,Tech Corp,master;phd,full,12000,12000
Nordic Innovation Grant,Norway,Nordic Council,master,partial,15000,5000
"""
    data = {
        'file': (io.BytesIO(csv_content.encode('utf-8')), 'custom_test.csv')
    }
    upload_res = client.post("/api/upload-dataset", data=data, content_type='multipart/form-data')
    assert upload_res.status_code == 200
    res_json = upload_res.get_json()
    assert res_json["stats"]["total_scholarships"] == 2

    # Verify custom dataset is queried
    query_res = client.get("/api/scholarships")
    assert query_res.get_json()["total"] == 2

    # Reset back to default
    reset_res = client.post("/api/reset-dataset")
    assert reset_res.status_code == 200
    assert reset_res.get_json()["stats"]["total_scholarships"] >= 20
