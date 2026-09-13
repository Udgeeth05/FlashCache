import hashlib
import hmac

from fastapi.testclient import TestClient

import main

from main import app


client = TestClient(
    app
)


READ_TOKEN = "flashcache-read-2026"

TENANT_ID = "negative-test"

NAMESPACE = "pytest"

HMAC_SECRET = "flashcache-hmac-secret-2026"


main.security.tokens = {
    "read": READ_TOKEN,
    "write": "flashcache-write-2026",
    "admin": "flashcache-admin-2026"
}

main.security.hmac_secret = HMAC_SECRET


def make_signature(product_id):

    message = (
        f"GET:"
        f"/product/{product_id}:"
        f"{TENANT_ID}:"
        f"{NAMESPACE}"
    )

    return hmac.new(
        HMAC_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def make_headers(product_id):

    return {
        "Authorization": (
            f"Bearer {READ_TOKEN}"
        ),
        "X-Tenant-ID": TENANT_ID,
        "X-Namespace": NAMESPACE,
        "X-Signature": make_signature(
            product_id
        )
    }


def test_negative_cache_api():

    product_id = 99999999

    first_response = client.get(
        f"/product/{product_id}",
        headers=make_headers(
            product_id
        )
    )

    assert first_response.status_code == 404

    assert (
        main.negative_cache.contains(
            f"{TENANT_ID}:"
            f"{NAMESPACE}:"
            f"{product_id}"
        )
        is True
    )

    second_response = client.get(
        f"/product/{product_id}",
        headers=make_headers(
            product_id
        )
    )

    assert second_response.status_code == 404

    assert (
        second_response.json()["detail"]
        == "Product not found"
    )