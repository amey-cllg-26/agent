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
    """Verify web application loads correctly with GCOEK branding."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Scholarship Finder for Government College of Engineering, Kolhapur" in response.data
    assert b"Profile & Filters" in response.data


def test_multipage_routes(client):
    """Verify all multi-page portal routes render successfully."""
    # Countries page
    res_countries = client.get("/countries")
    assert res_countries.status_code == 200
    assert b"Browse Scholarships by Destination Country" in res_countries.data
    assert b"Government College of Engineering, Kolhapur" in res_countries.data

    # GCOEK Guide page
    res_guide = client.get("/guide")
    assert res_guide.status_code == 200
    assert b"Higher Studies &amp; International Scholarships" in res_guide.data or b"Higher Studies & International Scholarships" in res_guide.data
    assert b"Shivaji University" in res_guide.data

    # Dataset manager page
    res_dataset = client.get("/dataset")
    assert res_dataset.status_code == 200
    assert b"Scholarship Dataset Management" in res_dataset.data

    # Advisor desk page
    res_advisor = client.get("/advisor")
    assert res_advisor.status_code == 200
    assert b"GCOEK Scholarship Advisor & Counseling Desk" in res_advisor.data

    # Individual scholarship detail page
    res_detail = client.get("/scholarship/DAAD%20WISE%20(Working%20Internships%20in%20Science%20and%20Engineering)")
    assert res_detail.status_code == 200
    assert b"DAAD WISE" in res_detail.data
    assert b"Government College of Engineering, Kolhapur" in res_detail.data


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


def test_india_portal_routes(client):
    """Verify Indian Caste & Category Schemes portal loads properly."""
    res_india = client.get("/india")
    assert res_india.status_code == 200
    assert b"Indian Caste &amp; Category-Based Scholarships" in res_india.data or b"Indian Caste & Category-Based Scholarships" in res_india.data
    assert b"Government College of Engineering, Kolhapur" in res_india.data
    assert b"MahaDBT" in res_india.data
    assert b"SC (Scheduled Caste)" in res_india.data


def test_india_scheme_detail(client):
    """Verify Indian scheme detail page loads with document checklist."""
    res_scheme = client.get("/india/scheme/1")
    assert res_scheme.status_code == 200
    assert b"Government of Maharashtra" in res_scheme.data
    assert b"Mandatory Verification Documents" in res_scheme.data


def test_india_api_filtering(client):
    """Verify Indian scholarship API filters by caste category and income limit."""
    # SC Category query
    res_sc = client.post("/api/india/scholarships", json={"category": "SC"})
    assert res_sc.status_code == 200
    data_sc = res_sc.get_json()
    assert data_sc["total"] > 0
    assert any("SC" in s["caste_category"] for s in data_sc["results"])

    # Income threshold query
    res_inc = client.post("/api/india/scholarships", json={"max_income": 200000})
    assert res_inc.status_code == 200
    data_inc = res_inc.get_json()
    assert all(s["max_income_inr"] == 0 or s["max_income_inr"] >= 200000 for s in data_inc["results"])

    # Stats query
    res_stats = client.get("/api/india/stats")
    assert res_stats.status_code == 200
    stats = res_stats.get_json()
    assert stats["total_schemes"] >= 90
    assert "SC" in stats["categories"]


def test_india_chat_advisory(client):
    """Verify advisor desk answers inquiries on MahaDBT and Indian caste scholarships."""
    payload = {
        "message": "What scholarships can an OBC engineering student get on MahaDBT with 3 lakh income at GCOEK?",
        "session_id": "test-caste-session"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert "MahaDBT" in data["reply"]
    assert "GCOEK" in data["reply"]


def test_mobile_navigation_markup(client):
    """Verify mobile hamburger button and responsive elements are present."""
    res = client.get("/")
    assert res.status_code == 200
    assert b'id="mobileMenuBtn"' in res.data
    assert b'class="mobile-menu-btn"' in res.data
    assert b'id="mainNavLinks"' in res.data
    assert b'fa-bars' in res.data


def test_deadline_not_zero(client):
    """Verify that no scholarship returns a 0.0 or 0 deadline."""
    res = client.get("/api/scholarships")
    assert res.status_code == 200
    items = res.get_json()["scholarships"]
    assert len(items) > 0
    for item in items:
        dl = str(item.get("deadline", "")).strip()
        assert dl != "0.0" and dl != "0", f"Broken deadline in {item['name']}: {dl}"
        assert dl != "", f"Empty deadline in {item['name']}"


def test_gpa_text_not_zero(client):
    """Verify that no recommendation or scholarship outputs ~0.0% text."""
    res = client.post("/api/recommend", json={"degree": "master", "cgpa": 8.0, "cgpa_scale": 10.0})
    assert res.status_code == 200
    data = res.get_json()
    items = data.get("results", [])
    for item in items:
        # Check warnings
        for w in item.get("warnings", []):
            assert "~0.0%" not in w and "0.0%" not in w, f"Found broken GPA text in warning: {w}"
        # Check gpa_requirement
        req = item.get("gpa_requirement", "")
        assert "~0.0%" not in req and "0.0%" not in req, f"Found broken GPA text in gpa_requirement: {req}"


def test_sorting_order(client):
    """Verify that recommendations are sorted by fit hierarchy (Target first)."""
    res = client.post("/api/recommend", json={"degree": "master", "cgpa": 8.0, "cgpa_scale": 10.0})
    assert res.status_code == 200
    results = res.get_json()["results"]
    assert len(results) > 0
    fits = [r["fit"] for r in results]
    # Check that Target occurs before Reach
    if "target" in fits and "reach" in fits:
        first_target = fits.index("target")
        first_reach = fits.index("reach")
        assert first_target <= first_reach, f"Target ({first_target}) should come before Reach ({first_reach})"


def test_last_verified_timestamp(client):
    """Verify that scholarships include a valid last_verified timestamp."""
    res = client.get("/api/scholarships")
    assert res.status_code == 200
    items = res.get_json()["scholarships"]
    assert len(items) > 0
    for item in items:
        lv = item.get("last_verified")
        assert lv is not None and lv != "", f"Missing last_verified in {item['name']}"
        assert "202" in lv, f"Expected valid year in last_verified: {lv}"





