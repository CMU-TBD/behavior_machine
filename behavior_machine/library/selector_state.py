from ..core import StateStatus, Board
from .sequential_state import SequentialState


class SelectorState(SequentialState):

    def execute(self, board: Board) -> StateStatus:
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
            # update flow_val & set the flow out to be the current flow
            flow_val = self._curr_child.flow_out
            # check if we are done because of interrupt
            if self.is_interrupted():
                return StateStatus.INTERRUPTED
            # get the current state
            status = self._curr_child._status
            if status == StateStatus.EXCEPTION:
                self.propergate_exception_information(self._curr_child)
                return StateStatus.EXCEPTION
            elif status == StateStatus.SUCCESS:
                self.flow_out = flow_val
                return status
            elif status == StateStatus.FAILED:
                pass
            else:
                # this really shouldn't happen.
                pass
        return StateStatus.FAILED
