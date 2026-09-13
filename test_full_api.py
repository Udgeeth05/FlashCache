import os


os.environ.setdefault(
    "FLASHCACHE_READ_TOKEN",
    "flashcache-read-2026"
)

os.environ.setdefault(
    "FLASHCACHE_WRITE_TOKEN",
    "flashcache-write-2026"
)

os.environ.setdefault(
    "FLASHCACHE_ADMIN_TOKEN",
    "flashcache-admin-2026"
)

os.environ.setdefault(
    "FLASHCACHE_HMAC_SECRET",
    "flashcache-hmac-secret-2026"
)


from fastapi.testclient import TestClient

from main import app


client = TestClient(
    app
)


READ_HEADERS = {
    "Authorization": (
        "Bearer flashcache-read-2026"
    ),
    "X-Tenant-ID": "test-tenant",
    "X-Namespace": "pytest"
}


WRITE_HEADERS = {
    "Authorization": (
        "Bearer flashcache-write-2026"
    ),
    "X-Tenant-ID": "test-tenant",
    "X-Namespace": "pytest"
}


ADMIN_HEADERS = {
    "Authorization": (
        "Bearer flashcache-admin-2026"
    ),
    "X-Tenant-ID": "test-tenant",
    "X-Namespace": "pytest"
}


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200


def test_readiness():

    response = client.get(
        "/ready"
    )

    assert response.status_code == 200


def test_cache_put_get_delete():

    key = "pytest-full-api"

    put_response = client.put(
        f"/v1/cache/{key}",
        headers=WRITE_HEADERS,
        json={
            "value": {
                "name": "FlashCache",
                "test": True
            },
            "ttl": 300
        }
    )

    assert put_response.status_code == 200

    get_response = client.get(
        f"/v1/cache/{key}",
        headers=READ_HEADERS
    )

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["status"] == "hit"

    assert data["value"]["name"] == "FlashCache"

    delete_response = client.delete(
        f"/v1/cache/{key}",
        headers=WRITE_HEADERS
    )

    assert delete_response.status_code == 200

    get_after_delete = client.get(
        f"/v1/cache/{key}",
        headers=READ_HEADERS
    )

    assert get_after_delete.status_code == 200

    assert (
        get_after_delete.json()["status"]
        == "miss"
    )


def test_missing_authentication():

    response = client.get(
        "/v1/cache/test-auth",
        headers={
            "X-Tenant-ID": "test-tenant",
            "X-Namespace": "pytest"
        }
    )

    assert response.status_code == 401


def test_read_token_cannot_write():

    response = client.put(
        "/v1/cache/test-rbac",
        headers=READ_HEADERS,
        json={
            "value": "forbidden",
            "ttl": 300
        }
    )

    assert response.status_code == 403


def test_missing_tenant():

    headers = {
        "Authorization": (
            "Bearer flashcache-write-2026"
        )
    }

    response = client.put(
        "/v1/cache/test-tenant",
        headers=headers,
        json={
            "value": "test",
            "ttl": 300
        }
    )

    assert response.status_code == 400


def test_idle_status():

    response = client.get(
        "/v1/cache/admin/idle-status",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        "idle_timeout_seconds"
        in data
    )

    assert (
        "check_interval_seconds"
        in data
    )

    assert "entries" in data