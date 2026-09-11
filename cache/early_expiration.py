import random
import time


class EarlyExpiration:

    def __init__(self, beta=1.0):
        self.beta = beta

    def should_refresh(self, expiration_time, fetch_time):

        now = time.time()

        remaining_ttl = expiration_time - now

        if remaining_ttl <= 0:
            return True

        if fetch_time <= 0:
            return False

        elapsed_time = fetch_time - remaining_ttl

        if elapsed_time <= 0:
            return False

        elapsed_ratio = elapsed_time / fetch_time

        probability = elapsed_ratio ** self.beta

        return random.random() < probability