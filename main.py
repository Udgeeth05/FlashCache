import os
import time
from fastapi import FastAPI
from cache.engine import CacheEngine

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

@app.get("/")
def home():
    return {
        "message": "FlashCache is running"
    }


@app.get("/product/{product_id}")
def get_product(product_id: int):

    start_time = time.perf_counter()

    # Check cache
    cached_product = cache.get(str(product_id))

    if cached_product is not None:

        latency = time.perf_counter() - start_time
        metrics.record_hit(latency)

        return {
            "source": "cache",
            "data": cached_product
        }

    # Cache miss → PostgreSQL
    db = SessionLocal()

    try:

        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        if product is None:

            latency = time.perf_counter() - start_time
            metrics.record_miss(latency)

            return {
                "error": "Product not found"
            }

        product_data = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "category": product.category
        }

        # Store in cache
        cache.put(
            str(product_id),
            product_data,
            ttl=60
        )

        latency = time.perf_counter() - start_time
        metrics.record_miss(latency)

        return {
            "source": "database",
            "data": product_data
        }

    finally:
        db.close()

@app.get("/stats")
def get_stats():
    return metrics.get_stats()

@app.get("/metrics")
def metrics():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )