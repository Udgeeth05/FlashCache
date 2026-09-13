import hashlib
import hmac
import threading

from fastapi.testclient import TestClient

import main
import cache.api as cache_api

from main import app


client = TestClient(
    app
)


TENANT_ID = "test-tenant"

NAMESPACE = "pytest"

PRODUCT_ID = 1

READ_TOKEN = "flashcache-read-2026"

WRITE_TOKEN = "flashcache-write-2026"

ADMIN_TOKEN = "flashcache-admin-2026"

HMAC_SECRET = "flashcache-hmac-secret-2026"


SECURITY_TOKENS = {
    "read": READ_TOKEN,
    "write": WRITE_TOKEN,
    "admin": ADMIN_TOKEN
}


# Configure the SecurityManager used by main.py.
main.security.tokens = SECURITY_TOKENS
main.security.hmac_secret = HMAC_SECRET


# Configure the separate SecurityManager used by
# cache/api.py.
cache_api.security.tokens = SECURITY_TOKENS
cache_api.security.hmac_secret = HMAC_SECRET


def build_signature():

    message = (
        f"GET:"
        f"/product/{PRODUCT_ID}:"
        f"{TENANT_ID}:"
        f"{NAMESPACE}"
    )

    return hmac.new(
        HMAC_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def make_request():

    response = client.get(
        f"/product/{PRODUCT_ID}",
        headers={
            "Authorization": (
                f"Bearer {READ_TOKEN}"
            ),
            "X-Tenant-ID": TENANT_ID,
            "X-Namespace": NAMESPACE,
            "X-Signature": build_signature()
        }
    )

    return response


def test_singleflight_api():

    results = [None] * 10

    errors = [None] * 10

    threads = []

    def worker(index):

        try:

            response = make_request()

            results[index] = response

        except Exception as error:

            errors[index] = error

    for index in range(10):

        thread = threading.Thread(
            target=worker,
            args=(index,)
        )

        threads.append(
            thread
        )

    for thread in threads:

        thread.start()

    for thread in threads:

        thread.join()

    for error in errors:

        assert error is None, (
            f"Request thread failed: {error}"
        )

    for response in results:

        assert response is not None

        assert response.status_code == 200, (
            f"Unexpected response: "
            f"{response.status_code} "
            f"{response.text}"
        )

        data = response.json()

        assert data["data"]["id"] == PRODUCT_ID

        assert data["tenant"] == TENANT_ID

        assert data["namespace"] == NAMESPACE

        assert data["source"] in (
            "cache",
            "database"
        )

    print(
        "SingleFlight API test completed"
    )