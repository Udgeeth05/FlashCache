import time

from cache.negative_cache import NegativeCache


def test_negative_cache_add_and_contains():

    cache = NegativeCache(
        ttl=2,
        capacity=100
    )

    cache.add("missing-key")

    assert cache.contains(
        "missing-key"
    ) is True


def test_negative_cache_expiration():

    cache = NegativeCache(
        ttl=0.1,
        capacity=100
    )

    cache.add("expired-key")

    assert cache.contains(
        "expired-key"
    ) is True

    time.sleep(0.2)

    assert cache.contains(
        "expired-key"
    ) is False


def test_negative_cache_remove():

    cache = NegativeCache(
        ttl=30,
        capacity=100
    )

    cache.add("remove-key")

    assert cache.contains(
        "remove-key"
    ) is True

    cache.remove(
        "remove-key"
    )

    assert cache.contains(
        "remove-key"
    ) is False


def test_negative_cache_capacity():

    cache = NegativeCache(
        ttl=30,
        capacity=2
    )

    cache.add("key-1")
    cache.add("key-2")
    cache.add("key-3")

    assert cache.size() == 2


def test_negative_cache_cleanup():

    cache = NegativeCache(
        ttl=0.1,
        capacity=100
    )

    cache.add("key-1")
    cache.add("key-2")

    time.sleep(0.2)

    removed = cache.cleanup()

    assert removed == 2

    assert cache.size() == 0