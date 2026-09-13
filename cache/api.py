from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Request,
    Security
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

from pydantic import BaseModel, Field

from cache.engine import CacheEngine
from cache.persistence import CachePersistence
from cache.security import SecurityManager
from cache.rate_limiter import TokenBucket
from cache.idle_eviction import IdleEvictionManager


router = APIRouter(
    prefix="/v1/cache",
    tags=["Cache"]
)


persistence = CachePersistence(
    directory="data"
)


cache = CacheEngine(
    capacity=100,
    policy="LRU",
    persistence=persistence
)


security = SecurityManager()


rate_limiter = TokenBucket(
    capacity=20,
    refill_rate=10
)


bearer_scheme = HTTPBearer(
    auto_error=False
)


class CacheValue(BaseModel):

    value: object

    ttl: int = Field(
        default=300,
        ge=1,
        le=86400
    )


def delete_cached_key(key):

    cache.delete(key)


idle_eviction = IdleEvictionManager(
    delete_callback=delete_cached_key,
    idle_timeout=600,
    check_interval=60
)


def require_token(
    credentials: HTTPAuthorizationCredentials | None,
    scope: str
):

    if credentials is None:

        raise HTTPException(
            status_code=401,
            detail="Missing API token"
        )

    if credentials.scheme.lower() != "bearer":

        raise HTTPException(
            status_code=401,
            detail="Invalid authorization scheme"
        )

    token = credentials.credentials

    if not security.has_scope(
        token,
        scope
    ):

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )


def validate_namespace(
    tenant_id: str | None,
    namespace: str | None
):

    if not tenant_id:

        raise HTTPException(
            status_code=400,
            detail="Missing X-Tenant-ID"
        )

    if not namespace:

        raise HTTPException(
            status_code=400,
            detail="Missing X-Namespace"
        )

    if len(tenant_id) > 64:

        raise HTTPException(
            status_code=400,
            detail="Invalid tenant ID"
        )

    if len(namespace) > 64:

        raise HTTPException(
            status_code=400,
            detail="Invalid namespace"
        )


def build_key(
    tenant_id: str,
    namespace: str,
    key: str
):

    return (
        f"{tenant_id}:"
        f"{namespace}:"
        f"{key}"
    )


@router.put("/{key}")
def put_cache(
    key: str,
    payload: CacheValue,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(
        bearer_scheme
    ),
    tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID"
    ),
    namespace: str | None = Header(
        default=None,
        alias="X-Namespace"
    )
):

    client_id = request.client.host

    if not rate_limiter.allow(
        client_id
    ):

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

    require_token(
        credentials,
        "write"
    )

    validate_namespace(
        tenant_id,
        namespace
    )

    cache_key = build_key(
        tenant_id,
        namespace,
        key
    )

    try:

        cache.put(
            cache_key,
            payload.value,
            ttl=payload.ttl
        )

        idle_eviction.track(
            cache_key
        )

    except ValueError as error:

        raise HTTPException(
            status_code=413,
            detail=str(error)
        )

    return {
        "status": "stored",
        "key": key,
        "tenant": tenant_id,
        "namespace": namespace,
        "ttl": payload.ttl
    }


@router.get("/{key}")
def get_cache(
    key: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(
        bearer_scheme
    ),
    tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID"
    ),
    namespace: str | None = Header(
        default=None,
        alias="X-Namespace"
    )
):

    client_id = request.client.host

    if not rate_limiter.allow(
        client_id
    ):

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

    require_token(
        credentials,
        "read"
    )

    validate_namespace(
        tenant_id,
        namespace
    )

    cache_key = build_key(
        tenant_id,
        namespace,
        key
    )

    value = cache.get(
        cache_key
    )

    if value is None:

        idle_eviction.remove(
            cache_key
        )

        return {
            "status": "miss",
            "key": key,
            "tenant": tenant_id,
            "namespace": namespace,
            "value": None
        }

    idle_eviction.track(
        cache_key
    )

    return {
        "status": "hit",
        "key": key,
        "tenant": tenant_id,
        "namespace": namespace,
        "value": value
    }


@router.delete("/{key}")
def delete_cache(
    key: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(
        bearer_scheme
    ),
    tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID"
    ),
    namespace: str | None = Header(
        default=None,
        alias="X-Namespace"
    )
):

    client_id = request.client.host

    if not rate_limiter.allow(
        client_id
    ):

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

    require_token(
        credentials,
        "write"
    )

    validate_namespace(
        tenant_id,
        namespace
    )

    cache_key = build_key(
        tenant_id,
        namespace,
        key
    )

    cache.delete(
        cache_key
    )

    idle_eviction.remove(
        cache_key
    )

    return {
        "status": "deleted",
        "key": key,
        "tenant": tenant_id,
        "namespace": namespace
    }


@router.get("/")
def cache_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(
        bearer_scheme
    ),
    tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID"
    ),
    namespace: str | None = Header(
        default=None,
        alias="X-Namespace"
    )
):

    client_id = request.client.host

    if not rate_limiter.allow(
        client_id
    ):

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

    require_token(
        credentials,
        "read"
    )

    validate_namespace(
        tenant_id,
        namespace
    )

    return {
        "status": "healthy",
        "tenant": tenant_id,
        "namespace": namespace,
        "cache_size": cache.size(),
        "idle_tracked_keys": len(
            idle_eviction.entries
        )
    }


@router.get("/admin/idle-status")
def idle_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(
        bearer_scheme
    ),
    tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID"
    ),
    namespace: str | None = Header(
        default=None,
        alias="X-Namespace"
    )
):

    client_id = request.client.host

    if not rate_limiter.allow(
        client_id
    ):

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

    require_token(
        credentials,
        "admin"
    )

    validate_namespace(
        tenant_id,
        namespace
    )

    return {
        "idle_timeout_seconds": (
            idle_eviction.idle_timeout
        ),
        "check_interval_seconds": (
            idle_eviction.check_interval
        ),
        "entries": (
            idle_eviction.get_status()
        )
    }