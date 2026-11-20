from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_root_returns_status_message(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "AI Intelligence Layer is running"}


def test_create_alert_returns_created_alert(client: TestClient) -> None:
    response = client.post(
        "/alerts/",
        json={
            "title": "CPU pressure",
            "severity": "critical",
            "source": "worker-1",
            "metric_name": "cpu_usage",
            "metric_value": 95,
            "threshold": 80,
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["severity"] == "critical"


def test_list_and_get_alert(client: TestClient) -> None:
    created = _create_alert(client)

    list_response = client.get("/alerts/")
    get_response = client.get(f"/alerts/{created['id']}")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == created["id"]
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Test alert"


def test_explain_alert_returns_explanation(client: TestClient) -> None:
    alert = _create_alert(client)

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert response.json()["alert_id"] == alert["id"]
    assert response.json()["explanation"] == (
        'This warning alert from test-source is titled "Test alert". '
        "The test_metric metric exceeded its threshold: the current value is 50.0, "
        "compared with a threshold of 40.0. Recommended next step: "
        "Review the affected system and monitor the metric closely. "
        "Acknowledged by: Not yet acknowledged."
    )
    assert "generated_at" in response.json()


# --- Edge cases added manually ---
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
    response = client.post("/alerts", json=payload)
    assert response.status_code == 201
    return response.json()


def test_explain_alert_for_nonexistent_id_returns_404(client: TestClient) -> None:
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
        source="api-gateway",
        metric_name="request_rate",
        metric_value=100,
        threshold=0,
    )

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert "explanation" in response.json()


def test_explain_alert_acknowledgement_defaults_when_unresolved(
    client: TestClient,
) -> None:
    alert = _create_alert(client)

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert response.json()["acknowledged"] is False