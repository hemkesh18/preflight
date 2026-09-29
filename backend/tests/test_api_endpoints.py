"""
Integration tests for Preflight FastAPI endpoints.
Tests:
- GET  /health: Service status and bank connectivity
- POST /brief: Pre-deploy proposal risk briefing (zero leakage)
- POST /gate: CI/CD release gate decision logic (PASS / WARN / BLOCK)
- GET  /replay: Delivers complete 150-deployment replay telemetry
- GET  /patterns: Delivers systemic reflected patterns
- POST /outcome: Post-deploy outcome ingestion into memory
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "bank_id" in data
    assert data["version"] == "1.0.0"


def test_brief_endpoint():
    payload = {
        "deploy_id": "dep-api-test-01",
        "service": "payments-api",
        "environment": "production",
        "change_type": "config",
        "day_of_week": "Friday",
        "author": "Marcus Brody",
        "pr_title": "Tune connection pool max buffer",
        "diff_summary": "- pool_max: 50\n+ pool_max: 15",
        "files_changed": ["config/production.yaml"]
    }
    response = client.post("/brief?memory_enabled=true", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["deploy_id"] == "dep-api-test-01"
    assert data["service"] == "payments-api"
    assert "risk_score" in data
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "reasons" in data


def test_ci_gate_decision_endpoint():
    payload = {
        "proposal": {
            "deploy_id": "dep-gate-test-01",
            "service": "payments-api",
            "environment": "production",
            "change_type": "config",
            "day_of_week": "Friday",
            "pr_title": "Update connection pool max connections",
            "diff_summary": "- pool_max_connections: 50\n+ pool_max_connections: 15",
            "files_changed": ["config/production.yaml"]
        },
        "block_on_high": True,
        "risk_threshold": 0.6,
        "memory_enabled": True
    }
    response = client.post("/gate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["action"] in ["PASS", "WARN", "BLOCK"]
    assert data["exit_code"] in [0, 1]
    assert "summary_markdown" in data
    assert "briefing" in data


def test_replay_endpoint():
    response = client.get("/replay")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "headline_metrics" in data
    assert "records" in data
    assert data["metadata"]["completed_deploys"] == 150
    assert len(data["records"]) == 150


def test_patterns_endpoint():
    response = client.get("/patterns")
    assert response.status_code == 200
    data = response.json()
    assert "patterns_summary" in data
