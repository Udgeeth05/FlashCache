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
from cache.negative_cache import NegativeCache
from cache.network_distributed_cache import (
    NetworkDistributedCache
)
from cache.api import router as cache_router
from cache.tracing import configure_tracing, tracer

from database import SessionLocal
from models import Product
from metrics import metrics


app = FastAPI(
    title="FlashCache API",
    version="1.0.0"
)


persistence = CachePersistence(
    directory="data"
)


# Local cache remains available as a fallback.
cache = CacheEngine(
    capacity=100,
    policy="LRU",
    persistence=persistence
)


# Main product cache.
# In Docker this automatically connects to:
# node-1, node-2 and node-3.
#
# When running locally without node URLs,
# it falls back to the local cache above.
product_cache = NetworkDistributedCache.from_environment(
    fallback_cache=cache
)


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


negative_cache = NegativeCache(
    ttl=30,
    capacity=10000
)


app.include_router(
    cache_router
)


configure_tracing(
    app
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

    with tracer.start_as_current_span(
        "flashcache.get_product"
    ) as span:

        span.set_attribute(
            "flashcache.product_id",
            product_id
        )

        span.set_attribute(
            "flashcache.tenant",
            tenant_id or ""
        )

        span.set_attribute(
            "flashcache.namespace",
            namespace or ""
        )

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

        if negative_cache.contains(
            key
        ):

            span.set_attribute(
                "flashcache.cache_result",
                "negative_hit"
            )

            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        with tracer.start_as_current_span(
            "flashcache.distributed_cache_get"
        ):

            cached_product = product_cache.get(
                key
            )

        if cached_product is not None:

            span.set_attribute(
                "flashcache.cache_result",
                "hit"
            )

            span.set_attribute(
                "flashcache.cache_node",
                product_cache.get_node(key) or ""
            )

            latency = (
                time.perf_counter()
                - start_time
            )

            metrics.record_hit(
                latency
            )

            metrics.update_cache_size(
                product_cache.size()
            )

            metrics.update_memory_bytes(
                product_cache.memory_bytes()
            )

            return {
                "source": "cache",
                "tenant": tenant_id,
                "namespace": namespace,
                "node": product_cache.get_node(
                    key
                ),
                "data": cached_product
            }

        span.set_attribute(
            "flashcache.cache_result",
            "miss"
        )

        if not circuit_breaker.allow_request():

            metrics.record_error()

            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable"
            )

        def load_from_database():

            with tracer.start_as_current_span(
                "flashcache.database_load"
            ):

                db = SessionLocal()

                try:

                    product = db.query(
                        Product
                    ).filter(
                        Product.id == product_id
                    ).first()

                    if product is None:

                        negative_cache.add(
                            key
                        )

                        return None

                    product_data = {
                        "id": product.id,
                        "name": product.name,
                        "price": product.price,
                        "category": product.category
                    }

                    negative_cache.remove(
                        key
                    )

                    with tracer.start_as_current_span(
                        "flashcache.distributed_cache_put"
                    ):

                        product_cache.put(
                            key,
                            product_data,
                            ttl=60
                        )

                    return product_data

                finally:

                    db.close()

        try:

            with tracer.start_as_current_span(
                "flashcache.singleflight"
            ):

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
            product_cache.size()
        )

        metrics.update_memory_bytes(
            product_cache.memory_bytes()
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
            "node": product_cache.get_node(
                key
            ),
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
            product_cache.size()
        )

        metrics.update_memory_bytes(
            product_cache.memory_bytes()
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
        ),
        "scores": (
            predictive_warmer.get_scores()
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
        product_cache.size()
    )

    metrics.update_memory_bytes(
        product_cache.memory_bytes()
    )

    return {
        **metrics.get_stats(),
        "distributed_nodes": (
            product_cache.get_nodes()
        ),
        "healthy_nodes": (
            product_cache.get_healthy_nodes()
        )
    }


@app.get("/metrics")
def metrics_endpoint():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )