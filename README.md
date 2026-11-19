# Alert Explainer API

## Purpose

A FastAPI service for creating and retrieving alerts and generating deterministic, rule-based explanations from an alert's severity, metric value, and threshold. Alert records are stored in a local SQLite database.

## Project Structure

```text
.
├── database.py                         # SQLite engine, session setup, and database dependency
├── main.py                             # FastAPI app and root endpoint
├── models.py                           # SQLAlchemy Alert model
├── requirements.txt                    # Runtime dependencies
├── schemas.py                          # Pydantic request and response schemas
├── test_alerts.py                      # API tests
├── routers/
│   └── alerts.py                       # Alert API endpoints
├── services/
│   └── explainer.py                    # Rule-based explanation generation
└── docs/
    └── adr/
        ├── 0001-rule-based-explanations.md
        └── 0002-human-approval-for-alert-summaries.md
```

## Alert Fields

| Field | Type | Description |
| --- | --- | --- |
| `id` | integer | Database-generated alert identifier. |
| `title` | string | Alert title. |
| `severity` | string | One of `critical`, `warning`, or `info`. |
| `source` | string | Alert source. |
| `metric_name` | string | Name of the metric associated with the alert. |
| `metric_value` | number | Current metric value. |
| `threshold` | number | Threshold used to evaluate the metric. |
| `created_at` | datetime | Database-generated creation time. |

When creating an alert, send `title`, `severity`, `source`, `metric_name`, `metric_value`, and `threshold`. The API assigns `id` and `created_at`.

## API Endpoints

| Method | Path | Status codes | Description |
| --- | --- | --- | --- |
| `GET` | `/` | `200` | Return the service status message. |
| `POST` | `/alerts/` | `201`, `422` | Create an alert; `422` indicates invalid request data. |
| `GET` | `/alerts/` | `200` | List alerts ordered by ID. |
| `GET` | `/alerts/{alert_id}` | `200`, `404`, `422` | Retrieve an alert; `404` if it does not exist and `422` if the path ID is invalid. |
| `POST` | `/alerts/{alert_id}/explain` | `200`, `404`, `422` | Generate an explanation; `404` if the alert does not exist and `422` if the path ID is invalid. |

Interactive API documentation is available at `/docs` when the service is running.

## Install and Run on Windows

In PowerShell, from the project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest httpx
python -m uvicorn main:app --reload
```

The API is served at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` for the interactive API documentation. The SQLite database file, `alerts.db`, is created in the working directory when the app initializes.

## Install and Run on Linux

In a Bash shell, from the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest httpx
python -m uvicorn main:app --reload
```

The API is served at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

## Run Tests

With the virtual environment activated, run:

```powershell
python -m pytest test_alerts.py -v
```

## Architecture Decision Records

- [0001: Rule-Based Explanations](docs/adr/0001-rule-based-explanations.md)
- [0002: Human Approval for Alert Summaries](docs/adr/0002-human-approval-for-alert-summaries.md)
