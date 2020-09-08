
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

    def load(self, path: str, direct: bool = True, namespace: str = "") -> bool:
        """Load a YAML file into the board.  Prefix with the namespace if it is not empty.

        Args:
            path (str): Path the the YAML file
            direct (bool, optional): Whether to save directly into board or under the key value of the path to the file. Defaults to True.
            namespace (str, optional): prefix to all the key values. Defaults to "".

        Returns:
            bool: Whether the load or read is successful.
        """
        import yaml

        try:
            with open(path, 'r') as load_file:
                obj = yaml.safe_load(load_file)
                if obj is None:
                    print("Read empty file.")
                    return False

                if direct:
                    if isinstance(obj, dict):
                        for key in obj.keys():
                            self.set(f"{namespace}.{key}" if namespace != "" else key, obj[key])
                    else:
                        self.set(f"{namespace}.{path}" if namespace != "" else path, obj)
                else:
                    self.set(path, obj)
                return True

        except OSError:
            print(f"Unable to read file:{path}.")
        
        return False

    def dump(self, path: str, namespace = "") -> bool:
        """Save the whole board into a YAML file. If namespace is not empty, 
        only keys starting with namespace will be saved.

        Args:
            path (str): Path to file
            namespace (str, optional): Namespace to select certain keys. Defaults to "".

        Returns:
            bool: Whether the save is successful.
        """
        import yaml

        # first we select the objects that will be saved
        save_map = self._map
        if namespace != "":
            save_map = {}
            with self._lock:
                key: str
                for key in self._map.keys():
                    if key.startswith(namespace):
                        save_map[key] = self._map[key]

        # now we save it to yaml
        try:
            with open(path, 'w') as dump_file:
                yaml.safe_dump(save_map, dump_file)
                return True
        except OSError as err:
            print(f"Unable to save board to {path}: {err}")
        return False