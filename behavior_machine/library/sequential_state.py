import threading
from ..core import StateStatus, State, NestedState
from ..board import Board
import typing


class SequentialState(NestedState):

    _children: typing.List[State]
    _curr_child: State
    _lock: threading.RLock

    def __init__(self, name, children: typing.List[State] = None):
        super(SequentialState, self).__init__(name)
        self._children = [] if children is None else children
        self._curr_child = None
        self._lock = threading.RLock()

    def add_children(self, state: State):
        self._children.append(state)

    def execute(self, board: Board):
        # execute each children one by one in order
        for child in self._children:
            with self._lock:
                # once we in lock, check if we are interrupted
                if self._interupted_event.is_set():
                    return StateStatus.INTERRUPTED
                self._curr_child = child
                self._curr_child.start(board)
            self._curr_child.wait()
            # check if we are done because of interrupt
            if self._interupted_event.is_set():
                return StateStatus.INTERRUPTED
            status = self._curr_child._status
            if status == StateStatus.EXCEPTIION:
                self.propergate_exception_information(self._curr_child)
                return StateStatus.EXCEPTIION
            elif status != StateStatus.SUCCESS:
                return status
        return StateStatus.SUCCESS

    def interrupt(self, timeout=None):
        self._interupted_event.set()
        with self._lock:
            try:
                self._curr_child.interrupt(timeout=timeout)
            except (AttributeError):
                # Attribution error happens if child node is empty
                # Possible race condition at the beginning where interupt gets call before we start initializing
                pass
        # wait for thread to end
        self._run_thread.join(timeout)
        return not self._run_thread.isAlive()

    def tick(self, board):
        next_state = super().tick(board)
        if next_state == self:
            with self._lock:
                self._curr_child.tick(board)
        return next_state

    def get_debug_info(self) -> typing.Dict[str, typing.Any]:

        self_info = super().get_debug_info()
        self_info['children'] = []
        for child in self._children:
            self_info['children'].append(child.get_debug_info())
        return self_info
