import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    def override_get_db():
        with Session(engine) as session:
            yield session

    try:
        Base.metadata.create_all(bind=engine)
        with monkeypatch.context() as overrides:
            overrides.setitem(app.dependency_overrides, get_db, override_get_db)
            with TestClient(app) as test_client:
                yield test_client
    finally:
        engine.dispose()


def _create_alert(client: TestClient, **overrides: str | float) -> dict: 
    """Create an alert through the API and return its JSON response.""" 
    payload: dict[str, str | float] = { 
        "title": "Test alert", 
        "severity": "warning", 
        "source": "test-source", 
        "metric_name": "test_metric", 
        "metric_value": 50.0, 
        "threshold": 40.0, 
    } 
    payload.update(overrides) 
    response = client.post("/alerts/", json=payload)
    assert response.status_code == 201 
    return response.json() 
  
  
def test_explain_alert_for_nonexistent_id_returns_404(client: TestClient)-> None: 
    response = client.post("/alerts/999/explain") 
  
    assert response.status_code == 404 
    assert response.json()["detail"] == "Alert not found" 
  
  
def test_explain_alert_when_metric_is_below_threshold( 
    client: TestClient, 
) -> None: 
    alert = _create_alert( 
        client, 
        title="Connection pool below minimum", 
        severity="warning", 
        source="db-pool", 
        metric_name="active_connections", 
        metric_value=2, 
        threshold=10, 
    ) 
  
    response = client.post(f"/alerts/{alert['id']}/explain") 
  
    assert response.status_code == 200 
    assert "fell below its threshold" in response.json()["explanation"] 
  
  
def test_explain_alert_with_zero_threshold_does_not_crash( 
    client: TestClient, 
) -> None: 
    alert = _create_alert( 
        client, 
        title="Unexpected traffic on idle endpoint", 
        severity="info",
        source="edge-cache",
        metric_name="request_count",
        metric_value=5,
        threshold=0,
    )

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert "threshold of 0.0" in response.json()["explanation"]
        
        