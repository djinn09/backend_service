from fastapi.testclient import TestClient
from datetime import date, timedelta
from app import schemas # For response model validation
from app.tests.conftest import MOCK_USER_ID # Get mock user ID

def test_create_sip_success(client: TestClient):
    sip_data = {
        "scheme_name": "Test Scheme 1",
        "monthly_amount": 1000,
        "start_date": str(date.today())
    }
    response = client.post("/sips/", json=sip_data, headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 201
    data = response.json()
    assert data["scheme_name"] == sip_data["scheme_name"]
    assert data["monthly_amount"] == sip_data["monthly_amount"]
    assert data["user_id"] == MOCK_USER_ID # Check if SIP is associated with the mock user

def test_create_sip_invalid_data(client: TestClient):
    response = client.post("/sips/", json={"scheme_name": "Test Scheme"}, headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation

def test_get_sips_summary_empty(client: TestClient):
    response = client.get("/sips/summary", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    assert response.json() == []

def test_get_sips_summary_one_sip(client: TestClient):
    start_date_val = date.today() - timedelta(days=60) # Approx 2 months ago
    sip_data = {"scheme_name": "Scheme Alpha", "monthly_amount": 500, "start_date": str(start_date_val)}
    client.post("/sips/", json=sip_data, headers={"Authorization": "Bearer fake-token"})

    response = client.get("/sips/summary", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    summary = response.json()
    assert len(summary) == 1
    # months_invested: (today.year - start.year)*12 + today.month - start.month + 1
    # If start_date_val is e.g. 2024-05-15 and today is 2024-07-15, months should be 3
    # If start_date_val is e.g. 2024-05-15 and today is 2024-07-10, months should be 3
    # If start_date_val is e.g. 2024-05-15 and today is 2024-05-30, months should be 1
    expected_months = (date.today().year - start_date_val.year) * 12 + (date.today().month - start_date_val.month) + 1
    assert summary[0]["scheme_name"] == "Scheme Alpha"
    assert summary[0]["months_invested"] == expected_months
    assert summary[0]["total_invested"] == 500 * expected_months

def test_get_sips_summary_multiple_sips_same_scheme(client: TestClient):
    s1_start = date.today() - timedelta(days=90) # ~3 months
    s2_start = date.today() - timedelta(days=30) # ~1 month
    client.post("/sips/", json={"scheme_name": "Scheme Beta", "monthly_amount": 1000, "start_date": str(s1_start)}, headers={"Authorization": "Bearer fake-token"})
    client.post("/sips/", json={"scheme_name": "Scheme Beta", "monthly_amount": 2000, "start_date": str(s2_start)}, headers={"Authorization": "Bearer fake-token"})

    response = client.get("/sips/summary", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    summary = response.json()
    assert len(summary) == 1

    s1_months = (date.today().year - s1_start.year) * 12 + (date.today().month - s1_start.month) + 1
    s2_months = (date.today().year - s2_start.year) * 12 + (date.today().month - s2_start.month) + 1

    expected_total_invested = (1000 * s1_months) + (2000 * s2_months)
    expected_max_months = max(s1_months, s2_months)

    assert summary[0]["scheme_name"] == "Scheme Beta"
    assert summary[0]["months_invested"] == expected_max_months
    assert summary[0]["total_invested"] == expected_total_invested

def test_get_sips_summary_sip_starts_future(client: TestClient):
    future_date = date.today() + timedelta(days=30)
    client.post("/sips/", json={"scheme_name": "Scheme Gamma", "monthly_amount": 100, "start_date": str(future_date)}, headers={"Authorization": "Bearer fake-token"})
    response = client.get("/sips/summary", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    # SIPs starting in future should not appear in summary, or have 0 invested based on current logic
    # Current logic in get_sips_summary filters out months_invested <= 0 before adding to summary_dict
    assert response.json() == []
