from fastapi.testclient import TestClient

from api import app


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_players_filters_documents_supported_query_params():
    with TestClient(app) as client:
        response = client.get("/players/filters")

    assert response.status_code == 200
    body = response.json()
    assert "season" in body["exact_filters"]
    assert "team" in body["exact_filters"]
    assert "overallAttribute" in body["range_filters"]
    assert body["pagination"]["default_limit"] == 25
    assert body["pagination"]["max_limit"] == 100
    assert "overallAttribute" in body["sorting"]["sortable_columns"]
    assert body["sorting"]["sort_orders"] == ["asc", "desc"]


def test_players_default_response_is_paginated():
    with TestClient(app) as client:
        response = client.get("/players")

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 25
    assert body["offset"] == 0
    assert body["total"] >= len(body["data"])
    assert len(body["data"]) <= 25


def test_players_can_filter_by_season_and_team():
    with TestClient(app) as client:
        response = client.get("/players?season=2025&team=Atlanta%20Hawks")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]
    assert all(player["season"] == 2025 for player in body["data"])
    assert all(player["team"].casefold() == "atlanta hawks" for player in body["data"])


def test_players_can_sort_by_overall_descending():
    with TestClient(app) as client:
        response = client.get("/players?limit=10&sort_by=overallAttribute&sort_order=desc")

    assert response.status_code == 200
    ratings = [player["overallAttribute"] for player in response.json()["data"]]
    assert ratings == sorted(ratings, reverse=True)


def test_players_rejects_unknown_filter():
    with TestClient(app) as client:
        response = client.get("/players?unknown=value")

    assert response.status_code == 400
    assert response.json()["detail"]["invalid_filters"] == ["unknown"]


def test_players_rejects_invalid_limit():
    with TestClient(app) as client:
        response = client.get("/players?limit=abc")

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid pagination parameters"


def test_players_rejects_limit_over_maximum():
    with TestClient(app) as client:
        response = client.get("/players?limit=101")

    assert response.status_code == 400


def test_players_rejects_invalid_sort_column():
    with TestClient(app) as client:
        response = client.get("/players?sort_by=badColumn")

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Unsupported sort column: badColumn"


def test_players_rejects_invalid_sort_order():
    with TestClient(app) as client:
        response = client.get("/players?sort_by=overallAttribute&sort_order=sideways")

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "sort_order must be 'asc' or 'desc'"
