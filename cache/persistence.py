import json
import os
import threading


class CachePersistence:

    def __init__(self, directory="data"):

        self.directory = directory

        self.aof_file = os.path.join(
            directory,
            "flashcache.aof"
        )

        self.snapshot_file = os.path.join(
            directory,
            "flashcache.rdb"
        )

        self.lock = threading.Lock()

        os.makedirs(
            directory,
            exist_ok=True
        )

    def append(
        self,
        operation,
        key,
        value=None,
        ttl=300
    ):

        record = {
            "operation": operation,
            "key": key,
            "value": value,
            "ttl": ttl
        }

        with self.lock:

            with open(
                self.aof_file,
                "a",
                encoding="utf-8"
            ) as file:

                file.write(
                    json.dumps(record) + "\n"
                )

    def snapshot(self, data):

        with self.lock:

            temporary_file = (
                self.snapshot_file + ".tmp"
            )

            with open(
                temporary_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file
                )

            os.replace(
                temporary_file,
                self.snapshot_file
            )

    def load_snapshot(self):

        if not os.path.exists(
            self.snapshot_file
        ):
            return {}

        with self.lock:

            with open(
                self.snapshot_file,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

    def load_aof(self):

        if not os.path.exists(
            self.aof_file
        ):
            return []

        records = []

        with self.lock:

            with open(
                self.aof_file,
                "r",
                encoding="utf-8"
            ) as file:

                for line in file:

                    line = line.strip()

                    if not line:
                        continue

                    records.append(
                        json.loads(line)
                    )

        return records

    def clear_aof(self):

        with self.lock:

            if os.path.exists(
                self.aof_file
            ):
                os.remove(
                    self.aof_file
                )