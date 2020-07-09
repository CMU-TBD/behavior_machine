
import threading
import typing


class Board():

    def __init__(self):
        self._map = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> typing.Any:
        with self._lock:
            return self._map.get(key, None)

    def set(self, key: str, value: typing.Any) -> None:
        with self._lock:
            self._map[key] = value
