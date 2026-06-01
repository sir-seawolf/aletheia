import os

import pytest
import requests


BASE_URL = os.getenv("ALETHEIA_API_BASE_URL", "http://127.0.0.1:8000")


def _api_available() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except requests.RequestException:
        return False


@pytest.mark.skipif(
    not _api_available(),
    reason="Aletheia API is not reachable on BASE_URL; skipping live integration test.",
)
def test_routing_policy_persist_and_ranking_endpoints():
    # 1) Set routing policy
    r = requests.patch(
        f"{BASE_URL}/api/settings/preferences",
        json={"section": "llm", "updates": {"routing_policy": "most_reliable"}},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True

    # 2) Refresh catalog
    r = requests.post(f"{BASE_URL}/api/llm/refresh_catalog", timeout=10)
    assert r.status_code == 200, r.text
    refresh = r.json()
    assert "providers" in refresh
    assert isinstance(refresh["providers"], list)

    # 3) Ranking with explicit policy
    r = requests.get(
        f"{BASE_URL}/api/llm/ranking",
        params={"policy": "most_reliable"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    ranking = r.json()

    assert ranking.get("policy") == "most_reliable"
    assert "ranking" in ranking and isinstance(ranking["ranking"], list)
    assert "available_count" in ranking
    assert "total_count" in ranking
    assert "refreshed_at" in ranking
