import os
import time
from fastapi import FastAPI
from cache.engine import CacheEngine
from cache.singleflight import SingleFlight

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

    product_data = singleflight.do(
        str(product_id),
        load_from_database
    )

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

@app.get("/stats")
def get_stats():
    return metrics.get_stats()

@app.get("/metrics")
def metrics_endpoint():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )