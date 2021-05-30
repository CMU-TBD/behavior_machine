from typing import Any
import typing
from ..core import StateStatus, State, Board
import copy


class IdleState(State):

    def __init__(self, name: str):
        """Constructor for IdleState. This state will always return StateStatus.RUNNING.

        Parameters
        ----------
        name : str
            Name of the State, useful in Debugging.
        """
        super().__init__(name)

    def execute(self, board):
        return StateStatus.RUNNING


class WaitState(State):
    """
    State that waits for X seconds before continuing
    """

    _duration: float
    _check_interval: float

    def __init__(self, name: str, duration: float):
        """Constructor for WaitState

        Parameters
        ----------
        name : str
            Name of the state, useful in Debugging
        duration : float
            Time to wait before returning from this state
        """
        self._duration = duration
        self._check_interval = 0.1
        super().__init__(name)

    def execute(self, board):

        # sleep by using interrupt's timeout
        if self._interupted_event.wait(self._duration):
            # this means an event was fired
            return StateStatus.INTERRUPTED
        else:
            # timeout
            return StateStatus.SUCCESS


class SaveFlowState(State):
    """
    State that saves the flow in variable into the board
    """

    _key: str

    def __init__(self, name: str, key: str):
        """Constructor for SaveFlowState

        Args:
            name (str): Name of the state.
            key (str): key to store the flow_in value.
        """
        self._key = key
        super().__init__(name)

    def execute(self, board: Board) -> StateStatus:
        if self.flow_in is None:
            return StateStatus.FAILED
        board.set(self._key, self.flow_in)
        return StateStatus.SUCCESS


class SetFlowState(State):
    """
    State that sets the flow with the value given in constructor
    """
    _val: Any

    def __init__(self, name: str, val: Any, deep_copy: bool = True):
        """Constructor for SetFlowState

        Args:
            name (str): Name of state.
            val (Any): Value to set flow_out to.
            deep_copy (bool, optional): Whether to deep copy the given value. Defaults to True.
        """
        if deep_copy:
            self._val = copy.deepcopy(val)
        else:
            self._val = val
        super().__init__(name)

    def execute(self, board: Board) -> StateStatus:

        self.flow_out = self._val
        return StateStatus.SUCCESS


class SetFlowFromBoardState(State):
    """
    State that sets the flow with the value stored in the board
    """
    _key: str

    def __init__(self, name: str, key: str):
        """Constructor for SetFlowState

        Args:
            name (str): Name of the state.
            key (str): Key to retrive value from board.
        """
        self._key = key
        super().__init__(name)

    def execute(self, board: Board) -> StateStatus:

        val = board.get(self._key)
        if val is None:
            return StateStatus.FAILED
        else:
            self.flow_out = val
            return StateStatus.SUCCESS


class SetBoardState(State):

    _val: typing.Any
    _key: str

    def __init__(self, name: str, key: str, val: Any = None):
        super().__init__(name)
        self._val = val
        self._key = key

    def execute(self, board: Board):
        if self._val is not None:
            # special case if the value is a lambda
            if callable(self._val):
                board.set(self._key, self._val())
            else:
                board.set(self._key, self._val)
        elif self.flow_in is not None:
            board.set(self._key, self.flow_in)
        else:
            return StateStatus.FAILED
        return StateStatus.SUCCESS


class GetBoardState(State):

    _key: str

    def __init__(self, name: str, key: str):
        super().__init__(name)
        self._key = key

    def execute(self, board: Board):
        self.flow_out = board.get(self._key)
        return StateStatus.SUCCESS
