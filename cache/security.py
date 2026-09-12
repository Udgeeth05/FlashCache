import hashlib
import hmac
import os
import secrets


class SecurityManager:

    def __init__(self):

        self.tokens = {
            "read": os.getenv("FLASHCACHE_READ_TOKEN"),
            "write": os.getenv("FLASHCACHE_WRITE_TOKEN"),
            "admin": os.getenv("FLASHCACHE_ADMIN_TOKEN")
        }

        self.hmac_secret = os.getenv(
            "FLASHCACHE_HMAC_SECRET"
        )

        self.max_payload_bytes = 5 * 1024 * 1024

    def validate_token(self, token):

        if not token:
            return None

        for scope, stored_token in self.tokens.items():

            if stored_token and secrets.compare_digest(
                token,
                stored_token
            ):
                return scope

        return None

    def has_scope(self, token, required_scope):

        scope = self.validate_token(token)

        if scope is None:
            return False

        if scope == "admin":
            return True

        if required_scope == "read":
            return scope in ("read", "write")

        if required_scope == "write":
            return scope == "write"

        if required_scope == "admin":
            return False

        return False

    def validate_hmac(self, message, signature):

        if not self.hmac_secret:
            return False

        if not signature:
            return False

        expected_signature = hmac.new(
            self.hmac_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(
            expected_signature,
            signature
        )

    def validate_payload_size(self, payload):

        if isinstance(payload, bytes):
            size = len(payload)
        else:
            size = len(str(payload).encode("utf-8"))

        return size <= self.max_payload_bytes