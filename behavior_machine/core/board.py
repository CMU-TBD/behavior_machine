import threading
import typing
import copy


class Board():

    def __init__(self):
        self._map = {}
        self._lock = threading.RLock()

    def get(self, key: str, deep_copy: bool = True) -> typing.Any:
        """Get the object associated with the key from the board. If the key doesn't exist, None is returned.
        By default, a deep copy of the object/variable is made. You can change this by setting deep_copy = False.

        Parameters
        ----------
        key : str
            Key used in the set function
        deep_copy : bool, optional
            Whether to create a deep_copy of the object, by default True

        Returns
        -------
        typing.Any
            The object/variable saved with the key.
        """
        with self._lock:
            if deep_copy:
                return copy.deepcopy(self._map.get(key, None))
            else:
                return self._map.get(key, None)

    def set(self, key: str, value: typing.Any, deep_copy: bool = True) -> None:
        """Save the object with the given key in the board. By default, a deep copy
        of the object is made. You can change this by setting deep_copy = False.
        There is no check for repetitions and newer objects will replace the old objects
        given the same key

        Parameters
        ----------
        key : str
            key to identify object in the board
        value : typing.Any
            object or variable to be saved
        deep_copy : bool, optional
            whether a deepcopy of the object/variable is made, by default True
        """
        with self._lock:
            if deep_copy:
                self._map[key] = copy.deepcopy(value)
            else:
                self._map[key] = value

    def exist(self, key: str) -> bool:
        """Checks whether a key already exist in the board.

        Parameters
        ----------
        key : str
            Key to check

        Returns
        -------
        bool
            True if the key exist in the board, False otherwise.
        """
        with self._lock:
            return key in self._map

    def load(self, keypair: typing.Mapping[str, typing.Any]) -> None:
        """deep copy a collection of key pairing into the board.

        Args:
            keypair (typing.Mapping[str, typing.Any]): Values to be copied in.
        """
        for key, item in keypair.items():
            self.set(key, item, deep_copy=True)
