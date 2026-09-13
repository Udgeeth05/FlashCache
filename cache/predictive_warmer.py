from collections import Counter


class PredictiveWarmer:

    def __init__(self, max_keys=10):

        self.max_keys = max_keys
        self.access_counts = Counter()

    def record_access(self, key):

        key = str(key)

        self.access_counts[key] += 1

    def get_hot_keys(self):

        hot_keys = self.access_counts.most_common(
            self.max_keys
        )

        return [
            key
            for key, count in hot_keys
        ]

    def get_access_counts(self):

        return dict(self.access_counts)

    def clear(self):

        self.access_counts.clear()