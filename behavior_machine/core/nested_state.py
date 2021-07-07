from .state_status import StateStatus
from .state import State
from .board import Board


class NestedState(State):

    _exception_raised_state_name: str  # The name of thrown state

    def __init__(self, name):
        self._exception_raised_state_name = ""
        super(NestedState, self).__init__(name)

    def propergate_exception_information(self, curr_state: State) -> None:
        self._internal_exception = curr_state._internal_exception

        # now we want to pass in the name of where it happened.
        # In the future, the states should know its own name, so they can descover it themselves
        try:
            if curr_state._exception_raised_state_name != "":
                self._exception_raised_state_name = f"{self._name}.{curr_state._exception_raised_state_name}"
            else:
                self._exception_raised_state_name = f"{self._name}.{curr_state._name}"
        except AttributeError:
            # _exception_raised_state_name doesn't exist
            self._exception_raised_state_name = f"{self._name}.{curr_state._name}"

    def _execute(self, board: Board):
        # use the base function
        super()._execute(board)
        if self._status == StateStatus.EXCEPTION:
            # If the current state exits due to an exception. It is unclear
            # if the lower/internal states stopped. We signal an interruption
            # to stop them.
            self.interrupt_internal_states()
            self.wait_for_internal_states()

    def interrupt(self, timeout: float = None) -> bool:
        return (self.interrupt_internal_states(timeout) and super().interrupt(timeout=timeout))

    def print_debugging_info(self):
        super().print_debugging_info()
        if self._internal_exception is not None:
            print(self._exception_raised_state_name)

    def wait_for_internal_states(self, timeout: float = None) -> bool:
        raise NotImplementedError("All nested state need to implement this method to test for completion.")

    def interrupt_internal_states(self, timeout: float = None) -> bool:
        raise NotImplementedError("All nested state need to implement this method to interrupt internal states.")
