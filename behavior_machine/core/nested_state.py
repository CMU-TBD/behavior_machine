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
        # Right now when it fails nothing goes up
        try:
            self.pre_execute()
            self._status = self.execute(board)
            self.post_execute()
        except Exception as e:
            try:
                self.interrupt()
            except RuntimeError as e2:
                if str(e2) != "cannot join current thread":
                    raise e2
                # this is a common exception because we are the current thread
                # This level of exception often happen in the transition checking level
            self._internal_exception = e
            self._status = StateStatus.EXCEPTION
        if self._status is None:
            self._status = StateStatus.NOT_SPECIFIED

    def print_debugging_info(self):
        super().print_debugging_info()
        if self._internal_exception is not None:
            print(self._exception_raised_state_name)
