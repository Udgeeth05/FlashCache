import time

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from cache.engine import CacheEngine
from cache.singleflight import SingleFlight
from cache.circuit_breaker import CircuitBreaker
from cache.cache_warmer import CacheWarmer
from cache.predictive_warmer import PredictiveWarmer
from cache.security import SecurityManager
from cache.rate_limiter import TokenBucket
from cache.persistence import CachePersistence
from cache.api import router as cache_router

from database import SessionLocal
from models import Product
from metrics import CacheMetrics


app = FastAPI(
    title="FlashCache API",
    version="1.0.0"
)


persistence = CachePersistence(
    directory="data"
)


cache = CacheEngine(
    capacity=100,
    policy="LRU",
    persistence=persistence
)


metrics = CacheMetrics()

singleflight = SingleFlight()

circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=10
)

cache_warmer = CacheWarmer(
    cache
)

predictive_warmer = PredictiveWarmer(
    max_keys=10
)

security = SecurityManager()

rate_limiter = TokenBucket(
    capacity=10,
    refill_rate=5
)


app.include_router(
    cache_router
)


def require_scope(
    authorization: str | None,
    required_scope: str
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Missing API token"
        )

    if not authorization.startswith(
        "Bearer "
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format"
        )

    token = authorization[7:]

    if not security.has_scope(
        token,
        required_scope
    ):

        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )


def check_rate_limit(
    request: Request
):

    client_id = request.client.host

    if not rate_limiter.allow(
        client_id
    ):

        metrics.record_error()

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )


def require_tenant(
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


def build_cache_key(
    tenant_id: str,
    namespace: str,
    key: str
):

    return (
        f"{tenant_id}:"
        f"{namespace}:"
        f"{key}"
    )


def require_hmac(
    request: Request,
    tenant_id: str,
    namespace: str,
    signature: str | None
):

    message = (
        f"{request.method}:"
        f"{request.url.path}:"
        f"{tenant_id}:"
        f"{namespace}"
    )

    if not security.validate_hmac(
        message,
        signature
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid HMAC signature"
        )


@app.get("/")
def home():

    return {
        "message": "FlashCache is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.get("/ready")
def readiness():

    if not circuit_breaker.allow_request():

        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )

    return {
        "status": "ready"
    }


@app.get("/product/{product_id}")
def get_product(
    product_id: int,
    request: Request,
    authorization: str | None = Header(
        default=None
    ),
    tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID"
    ),
    namespace: str | None = Header(
        default=None,
        alias="X-Namespace"
    ),
    signature: str | None = Header(
        default=None,
        alias="X-Signature"
    )
):

    check_rate_limit(
        request
    )

    require_scope(
        authorization,
        "read"
    )

    require_tenant(
        tenant_id,
        namespace
    )

    require_hmac(
        request,
        tenant_id,
        namespace,
        signature
    )

    start_time = time.perf_counter()

    key = build_cache_key(
        tenant_id,
        namespace,
        str(product_id)
    )

    predictive_warmer.record_access(
        key
    )

    cached_product = cache.get(
        key
    )

    if cached_product is not None:

        latency = (
            time.perf_counter()
            - start_time
        )

        metrics.record_hit(
            latency
        )

        metrics.update_cache_size(
            cache.size()
        )

        metrics.update_memory_bytes(
            cache.memory_bytes()
        )

        return {
            "source": "cache",
            "tenant": tenant_id,
            "namespace": namespace,
            "data": cached_product
        }

    if not circuit_breaker.allow_request():

        metrics.record_error()

        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable"
        )

    def load_from_database():

        db = SessionLocal()

        try:

            product = db.query(
                Product
            ).filter(
                Product.id == product_id
            ).first()

            if product is None:

                return None

            product_data = {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "category": product.category
            }

            cache.put(
                key,
                product_data,
                ttl=60
            )

            return product_data

        finally:

            db.close()

    try:

        product_data = singleflight.do(
            key,
            load_from_database
        )

        circuit_breaker.record_success()

    except Exception:

        circuit_breaker.record_failure()

        metrics.record_error()

        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable"
        )

    latency = (
        time.perf_counter()
        - start_time
    )

    metrics.record_miss(
        latency
    )

    metrics.update_cache_size(
        cache.size()
    )

    metrics.update_memory_bytes(
        cache.memory_bytes()
    )

    if product_data is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return {
        "source": "database",
        "tenant": tenant_id,
        "namespace": namespace,
        "data": product_data
    }


@app.post("/warm")
def warm_cache(
    request: Request,
    authorization: str | None = Header(
        default=None
    ),
    tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID"
    ),
    namespace: str | None = Header(
        default=None,
        alias="X-Namespace"
    ),
    signature: str | None = Header(
        default=None,
        alias="X-Signature"
    )
):

    check_rate_limit(
        request
    )

    require_scope(
        authorization,
        "write"
    )

    require_tenant(
        tenant_id,
        namespace
    )

    require_hmac(
        request,
        tenant_id,
        namespace,
        signature
    )

    if not circuit_breaker.allow_request():

        metrics.record_error()

        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable"
        )

    hot_keys = (
        predictive_warmer.get_hot_keys()
    )

    def load_product(key):

        db = SessionLocal()

        try:

            product_id = int(
                key.split(":")[-1]
            )

            product = db.query(
                Product
            ).filter(
                Product.id == product_id
            ).first()

            if product is None:

                return None

            return {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "category": product.category
            }

        finally:

            db.close()

    try:

        result = cache_warmer.warm(
            keys=hot_keys,
            loader=load_product,
            ttl=60
        )

        circuit_breaker.record_success()

        metrics.update_cache_size(
            cache.size()
        )

        metrics.update_memory_bytes(
            cache.memory_bytes()
        )

        return {
            "predicted_keys": hot_keys,
            "warming": result
        }

    except Exception:

        circuit_breaker.record_failure()

        metrics.record_error()

        raise HTTPException(
            status_code=503,
            detail="Cache warming failed"
        )


@app.get("/predict")
def get_predictions(
    request: Request,
    authorization: str | None = Header(
        default=None
    ),
    tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID"
    ),
    namespace: str | None = Header(
        default=None,
        alias="X-Namespace"
    ),
    signature: str | None = Header(
        default=None,
        alias="X-Signature"
    )
):

    check_rate_limit(
        request
    )

    require_scope(
        authorization,
        "read"
    )

    require_tenant(
        tenant_id,
        namespace
    )

    require_hmac(
        request,
        tenant_id,
        namespace,
        signature
    )

    return {
        "tenant": tenant_id,
        "namespace": namespace,
        "hot_keys": (
            predictive_warmer.get_hot_keys()
        ),
        "access_counts": (
            predictive_warmer.get_access_counts()
        )
    }


@app.get("/stats")
def get_stats(
    request: Request,
    authorization: str | None = Header(
        default=None
    ),
    tenant_id: str | None = Header(
        default=None,
        alias="X-Tenant-ID"
    ),
    namespace: str | None = Header(
        default=None,
        alias="X-Namespace"
    ),
    signature: str | None = Header(
        default=None,
        alias="X-Signature"
    )
):

    check_rate_limit(
        request
    )

    require_scope(
        authorization,
        "read"
    )

    require_tenant(
        tenant_id,
        namespace
    )

    require_hmac(
        request,
        tenant_id,
        namespace,
        signature
    )

    metrics.update_cache_size(
        cache.size()
    )

    metrics.update_memory_bytes(
        cache.memory_bytes()
    )

    return metrics.get_stats()


@app.get("/metrics")
def metrics_endpoint():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )