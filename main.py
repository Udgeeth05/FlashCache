import os
import time
from fastapi import FastAPI
from cache.engine import CacheEngine
from cache.singleflight import SingleFlight
from cache.circuit_breaker import CircuitBreaker
from cache.cache_warmer import CacheWarmer
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from database import SessionLocal
from models import Product
from metrics import CacheMetrics

app = FastAPI()

cache = CacheEngine(
    capacity=100,
    policy="LRU"
)

metrics = CacheMetrics()

singleflight = SingleFlight()

circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=10
)

cache_warmer = CacheWarmer(cache)


@app.get("/")
def home():
    return {
        "message": "FlashCache is running"
    }


@app.get("/product/{product_id}")
def get_product(product_id: int):

    start_time = time.perf_counter()

    cached_product = cache.get(str(product_id))

    if cached_product is not None:

        latency = time.perf_counter() - start_time
        metrics.record_hit(latency)

        return {
            "source": "cache",
            "data": cached_product
        }

    if not circuit_breaker.allow_request():
        return {
            "error": "Database temporarily unavailable"
        }

    def load_from_database():

        db = SessionLocal()

        try:

            product = db.query(Product).filter(
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
                str(product_id),
                product_data,
                ttl=60
            )

            return product_data

        finally:
            db.close()

    try:

        product_data = singleflight.do(
            str(product_id),
            load_from_database
        )

        circuit_breaker.record_success()

    except Exception:

        circuit_breaker.record_failure()

        return {
            "error": "Database temporarily unavailable"
        }

    latency = time.perf_counter() - start_time
    metrics.record_miss(latency)

    if product_data is None:
        return {
            "error": "Product not found"
        }

    return {
        "source": "database",
        "data": product_data
    }


@app.post("/warm")
def warm_cache():

    if not circuit_breaker.allow_request():
        return {
            "error": "Database temporarily unavailable"
        }

    def load_product(key):

        db = SessionLocal()

        try:

            product = db.query(Product).filter(
                Product.id == int(key)
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
            keys=["1", "2", "3"],
            loader=load_product,
            ttl=60
        )

        circuit_breaker.record_success()

        return result

    except Exception:

        circuit_breaker.record_failure()

        return {
            "error": "Cache warming failed"
        }


@app.get("/stats")
def get_stats():
    return metrics.get_stats()


@app.get("/metrics")
def metrics_endpoint():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )