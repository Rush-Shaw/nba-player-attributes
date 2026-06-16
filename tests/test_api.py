from fastapi.testclient import TestClient

from api import app


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
