import hashlib
import hmac
import urllib.request
import urllib.error


BASE_URL = "http://127.0.0.1:8000"

HMAC_SECRET = "flashcache-hmac-secret-2026"


def signature(method, path, tenant, namespace):

    message = (
        f"{method}:"
        f"{path}:"
        f"{tenant}:"
        f"{namespace}"
    )

    return hmac.new(
        HMAC_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


def request(
    method,
    path,
    token,
    tenant,
    namespace
):

    sig = signature(
        method,
        path,
        tenant,
        namespace
    )

    req = urllib.request.Request(
        BASE_URL + path,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": tenant,
            "X-Namespace": namespace,
            "X-Signature": sig
        }
    )

    try:

        with urllib.request.urlopen(req) as response:

            print(
                method,
                path,
                "→",
                response.status
            )

            print(
                response.read().decode()
            )

    except urllib.error.HTTPError as error:

        print(
            method,
            path,
            "→",
            error.code
        )

        print(
            error.read().decode()
        )


print("==============================")
print("FlashCache Security Test")
print("==============================")


print("\nValid tenant request:")

request(
    "GET",
    "/product/1",
    "flashcache-read-2026",
    "tenant-a",
    "products"
)


print("\nSecond tenant:")

request(
    "GET",
    "/product/1",
    "flashcache-read-2026",
    "tenant-b",
    "products"
)


print("\nInvalid HMAC:")

req = urllib.request.Request(
    BASE_URL + "/product/1",
    headers={
        "Authorization": "Bearer flashcache-read-2026",
        "X-Tenant-ID": "tenant-a",
        "X-Namespace": "products",
        "X-Signature": "invalid-signature"
    }
)

try:

    with urllib.request.urlopen(req) as response:
        print("Unexpected:", response.status)

except urllib.error.HTTPError as error:

    print(
        "Invalid HMAC →",
        error.code
    )

    print(
        error.read().decode()
    )


print("\nMissing tenant:")

request(
    "GET",
    "/product/1",
    "flashcache-read-2026",
    "",
    "products"
)