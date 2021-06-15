import threading
from ..core import StateStatus, State, NestedState, Board
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

    def pre_execute(self):
        # make sure all children states have the correct states
        child: State
        for child in self._children:
            child._status = StateStatus.NOT_RUNNING
        return super().pre_execute()

    def execute(self, board: Board) -> StateStatus:
        flow_val = self.flow_in
        # execute each children one by one in order
        for child in self._children:
            with self._lock:
                # once we in lock, check if we are interrupted
                if self.is_interrupted():
                    return StateStatus.INTERRUPTED
                self._curr_child = child
                self._curr_child.start(board, flow_val)
            self._curr_child.wait()
            # check if we are done because of interrupt
            if self.is_interrupted():
                return StateStatus.INTERRUPTED
            status = self._curr_child._status
            if status == StateStatus.EXCEPTION:
                self.propergate_exception_information(self._curr_child)
                return StateStatus.EXCEPTION
            elif status != StateStatus.SUCCESS:
                return status
            # update flow_val & set the flow out to be the current flow
            flow_val = self._curr_child.flow_out
            self.flow_out = flow_val
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
        # now we call the parent function to clear the running thread
        return super().interrupt(timeout)

    def tick(self, board):
        next_state = super().tick(board)
        if next_state == self:
            with self._lock:
                # TODO: Reexamine if this will be a problem.
                # There might be a race condition where sequential state is tick() before the actual execution.
                if self._curr_child is not None:
                    self._curr_child.tick(board)
        return next_state

    def get_debug_info(self) -> typing.Dict[str, typing.Any]:

        self_info = super().get_debug_info()
        self_info['children'] = []
        for child in self._children:
            self_info['children'].append(child.get_debug_info())
        return self_info
