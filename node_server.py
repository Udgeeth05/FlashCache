import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cache.engine import CacheEngine


NODE_ID = os.getenv(
    "NODE_ID",
    "node-1"
)

CACHE_CAPACITY = int(
    os.getenv(
        "CACHE_CAPACITY",
        "1000"
    )
)


app = FastAPI(
    title="FlashCache Node",
    version="1.0.0"
)


cache = CacheEngine(
    capacity=CACHE_CAPACITY,
    policy="LRU"
)


class CacheValue(BaseModel):

    value: object

    ttl: int = 300


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "node": NODE_ID
    }


@app.get("/node")
def node_info():

    return {
        "node": NODE_ID,
        "cache_size": cache.size(),
        "memory_bytes": cache.memory_bytes()
    }


@app.get("/cache/{key}")
def get_cache(
    key: str
):

    value = cache.get(
        key
    )

    if value is None:

        raise HTTPException(
            status_code=404,
            detail="Cache miss"
        )

    return {
        "node": NODE_ID,
        "key": key,
        "value": value
    }


@app.put("/cache/{key}")
def put_cache(
    key: str,
    payload: CacheValue
):

    cache.put(
        key,
        payload.value,
        payload.ttl
    )

    return {
        "status": "stored",
        "node": NODE_ID,
        "key": key,
        "ttl": payload.ttl
    }


@app.delete("/cache/{key}")
def delete_cache(
    key: str
):

    cache.delete(
        key
    )

    return {
        "status": "deleted",
        "node": NODE_ID,
        "key": key
    }