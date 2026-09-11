import threading


class SingleFlight:

    def __init__(self):

        self.lock = threading.Lock()

        self.calls = {}

    def do(self, key, function):

        with self.lock:

            if key in self.calls:

                call = self.calls[key]

                is_first = False

            else:

                call = {
                    "event": threading.Event(),
                    "result": None,
                    "error": None
                }

                self.calls[key] = call

                is_first = True

        # First request performs the expensive operation.
        if is_first:

            try:

                call["result"] = function()

            except Exception as error:

                call["error"] = error

            finally:

                call["event"].set()

                with self.lock:

                    self.calls.pop(key, None)

            if call["error"]:

                raise call["error"]

            return call["result"]

        # Other requests wait for the first request.
        call["event"].wait()

        if call["error"]:

            raise call["error"]

        return call["result"]