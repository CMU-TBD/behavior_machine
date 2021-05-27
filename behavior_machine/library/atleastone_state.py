import sys

from ..core import StateStatus, Board
from .parallel_state import ParallelState


class AtLeastOneState(ParallelState):
    """ An extension of parallel state where it stops and return if at least one of the children state
    is successful.
    """

    def _statestatus_criteria(self) -> StateStatus:
        # check the state of all the children & return success if and only if all are successful
        for child in self._children:
            if child.check_status(StateStatus.SUCCESS):
                return StateStatus.SUCCESS
        return StateStatus.FAILED

    def tick(self, board: Board):
        # Note, this is very similar to the ParallelState tick function. Any fixes should also be applied there.
        # check if we should transition out of this state
        next_state = super().tick(board)
        if next_state == self:
            # we are staying in this state, tick each of the child
            at_least_one_running = False
            for child in self._children:
                # if the child is running, tick it
                if child.check_status(StateStatus.RUNNING):
                    at_least_one_running = True
                    child.tick(board)
                elif child.check_status(StateStatus.SUCCESS):
                    self._children_complete_event.set()
                elif child.check_status(StateStatus.EXCEPTION):
                    self.propergate_exception_information(child)
                    self._child_exception = True
                    self._children_complete_event.set()
                # elif child.check_status(StateStatus.NOT_RUNNING):
                #     # This is likely an edge case where the child hasn't start being check yet.
                #     at_least_one_running = True
            # if all child already done, we need to let the main process knows
            if not at_least_one_running:
                self._children_complete_event.set()
            # return itself since nothing transitioned
            return self
        else:
            # we are going to a new start, interrupt everthing that is going on
            if not self.interrupt():
                # we wasn't able to complete the interruption.
                # This is bad.. meaning there are bunch of zombie threads running about
                print(
                    f"ERROR {self._name} of type {self.__class__} unable to complete Interrupt Action. \
                        Zombie threads likely", file=sys.stderr)
            return next_state
