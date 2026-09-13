import time

from cache.predictive_warmer import PredictiveWarmer


def test_record_access():

    warmer = PredictiveWarmer(
        max_keys=3
    )

    warmer.record_access(
        "key-1"
    )

    warmer.record_access(
        "key-1"
    )

    warmer.record_access(
        "key-2"
    )

    counts = warmer.get_access_counts()

    assert counts["key-1"] == 2

    assert counts["key-2"] == 1


def test_hot_keys():

    warmer = PredictiveWarmer(
        max_keys=2
    )

    for _ in range(5):

        warmer.record_access(
            "hot-key"
        )

    warmer.record_access(
        "cold-key"
    )

    hot_keys = warmer.get_hot_keys()

    assert "hot-key" in hot_keys


def test_max_keys():

    warmer = PredictiveWarmer(
        max_keys=2
    )

    warmer.record_access("key-1")
    warmer.record_access("key-2")
    warmer.record_access("key-3")

    hot_keys = warmer.get_hot_keys()

    assert len(hot_keys) == 2


def test_time_decay():

    warmer = PredictiveWarmer(
        max_keys=2,
        decay_rate=1.0
    )

    warmer.record_access(
        "old-key"
    )

    time.sleep(0.2)

    warmer.record_access(
        "new-key"
    )

    scores = warmer.get_scores()

    assert scores["new-key"] > scores["old-key"]


def test_remove():

    warmer = PredictiveWarmer()

    warmer.record_access(
        "key-1"
    )

    warmer.remove(
        "key-1"
    )

    assert (
        warmer.size()
        == 0
    )


def test_clear():

    warmer = PredictiveWarmer()

    warmer.record_access(
        "key-1"
    )

    warmer.record_access(
        "key-2"
    )

    warmer.clear()

    assert (
        warmer.size()
        == 0
    )