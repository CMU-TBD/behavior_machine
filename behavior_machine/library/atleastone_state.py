from ..core import StateStatus, State
from .parallel_state import ParallelState


class AtLeastOneState(ParallelState):
    """ An extension of parallel state where it stops and return if at least one of the children state
    is successful.
    """

    def _statestatus_criteria(self) -> StateStatus:
        # check the state of all the children & return success if at least one child succeed.
        for child in self._children:
            if child.check_status(StateStatus.SUCCESS):
                return StateStatus.SUCCESS
        return StateStatus.FAILED

    def _tick_child_complete_function(self, child_state: State) -> bool:
        return child_state.check_status(StateStatus.SUCCESS)
