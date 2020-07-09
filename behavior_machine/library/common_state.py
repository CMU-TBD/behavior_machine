from ..core import StateStatus, State


class IdleState(State):

    def __init__(self, name: str):
        """Constructor for IdleState

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
            Time to wait before returnning from this state
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
