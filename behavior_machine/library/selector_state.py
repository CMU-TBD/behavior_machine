import threading
from ..core import StateStatus, State, NestedState, Board
from .sequential_state import SequentialState
import typing


class SelectorState(SequentialState):

    def execute(self, board: Board):
        flow_val = self.flow_in
        # execute each children one by one in order until one success.
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
            # get the current state
            status = self._curr_child._status
            if status == StateStatus.EXCEPTION:
                self.propergate_exception_information(self._curr_child)
                return StateStatus.EXCEPTION
            elif status == StateStatus.SUCCESS:
                return status
            elif status == StateStatus.FAILED:
                pass
            else:
                # this really shouldn't happen.
                pass

            # update flow_val
            flow_val = self._curr_child.flow_out
        return StateStatus.FAILED
