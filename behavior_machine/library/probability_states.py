import threading
from ..core import StateStatus, State, NestedState, Board
import typing
import random
import threading

class RandomPickState(NestedState):

    _picked_state: State
    _children: typing.Sequence[State]
    _lock: threading.RLock

    def __init__(self, children: typing.Sequence[State],name = ""):
        self._children = children
        self._picked_state = None
        self._lock = threading.RLock()
        super().__init__(name)

    def execute(self, board: Board) -> StateStatus:

        with self._lock:
            self._picked_state = random.choice(self._children)
        self._picked_state.start(board)
        
        self._picked_state.wait()

        # set the flow out and pass the status out.
        self.flow_out = self._picked_state.flow_out
        result_status = self._picked_state.get_status()
        with self._lock:
            self._picked_state = None
        return result_status

    def interrupt(self, timeout: float = None) -> bool:
        # we have a lock here just in case it suddenly become None when interrupting.
        self.signal_interrupt()
        with self._lock:
            if self._picked_state is not None:
                return self._picked_state.interrupt(timeout)
        return True
