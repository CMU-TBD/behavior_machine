import threading
from ..core import StateStatus, State, NestedState, Board
import typing
import sys


class ParallelState(NestedState):

    _children: typing.List[State]
    _thread_list: list
    _state_complete_event: threading.Event
    _child_exception: bool

    def __init__(self, name, children: list = None):
        super(ParallelState, self).__init__(name)
        self._children = [] if children is None else children
        self._state_complete_event = threading.Event()
        self._child_exception = False

    def add_children(self, state: State):
        self._children.append(state)

    def pre_execute(self):
        # make sure all children states have the correct states
        child: State
        for child in self._children:
            child._status = StateStatus.NOT_RUNNING
        # clear the event flag before starting
        self._state_complete_event.clear()
        self._child_exception = False
        return super().pre_execute()

    def interrupt_internal_states(self, timeout: float = None) -> bool:
        # we send the interrupt signal to all children that are running
        for child in self._children:
            if child.check_status(StateStatus.RUNNING):
                child.signal_interrupt()
        # now we wait for each children
        failed = False
        for child in self._children:
            if not child.interrupt(timeout):
                print(f"ERROR {self.get_debug_name()} unable to complete Interrupt Action \
                    for child {child.get_debug_name()} Zombie threads likely", file=sys.stderr)
                failed = True
            if child.check_status(StateStatus.EXCEPTION):
                # this is the child that thrown an exception
                # we propergate the information upwards.
                self.propergate_exception_information(child)
        return not failed

    def wait_for_internal_states(self, timeout: float = None) -> bool:
        for child in self._children:
            if not child.wait(timeout):
                return False
        return True

    def interrupt(self, timeout: float = None) -> bool:
        # set our own flag to be true
        self._interupted_event.set()
        # set that the state should be finishing
        self._state_complete_event.set()
        # we wait for the main thread to stop
        return super().interrupt(timeout=timeout)

    def _statestatus_criteria(self) -> StateStatus:
        # check the state of all the children & return success if and only if all are successful
        all_success = True
        for child in self._children:
            if not child.check_status(StateStatus.SUCCESS):
                all_success = False
        return StateStatus.SUCCESS if all_success else StateStatus.FAILED

    def _tick_child_complete_function(self, child_state: State) -> bool:
        return child_state.check_status(StateStatus.FAILED)

    def execute(self, board: Board) -> StateStatus:

        # start each child.
        for child in self._children:
            # because each child starts their own thread, no extra management required.
            child.start(board)

        # we wait for when this state should be completed
        self._state_complete_event.wait()
        # we now interrupt and stop all remaining running state
        self.interrupt_internal_states()
        # if we were interrupted
        if self.is_interrupted():
            return StateStatus.INTERRUPTED
        # if an exception occur in one of the child states
        if self._child_exception:
            return StateStatus.EXCEPTION
        # based on the criteria, return the status
        return self._statestatus_criteria()

    def tick(self, board: Board):
        # Note, this is very similar to the AtLeastOneState's tick function. Any fixes should also be applied there.
        # check if we should transition out of this state
        next_state = super().tick(board)
        if next_state == self:
            # we are staying in this state.
            # If we are currently trying to resolve interrupt, return self.
            if self.is_interrupted():
                return self
            # we are staying in this state, tick each of the children.
            at_least_one_running = False
            for child in self._children:
                # if the child is running, tick it
                if child.check_status(StateStatus.RUNNING):
                    at_least_one_running = True
                    child.tick(board)
                elif self._tick_child_complete_function(child):
                    # one state failed, this state is now over.
                    self._state_complete_event.set()
                elif child.check_status(StateStatus.EXCEPTION):
                    self.propergate_exception_information(child)
                    self._child_exception = True
                    self._state_complete_event.set()
                elif child.check_status(StateStatus.NOT_RUNNING):
                    # This is likely an edge case where the child hasn't start being check yet.
                    at_least_one_running = True
            # if all child already done, we need to let the main process knows
            if not at_least_one_running:
                self._state_complete_event.set()
            # return itself since nothing transitioned
            return self
        else:
            # we are transitioning out. let's interrupt the children running.
            # TODO: this blocks the executing of the tick.
            self.interrupt()
            return next_state

    def get_debug_info(self) -> typing.Dict[str, typing.Any]:

        self_info = super().get_debug_info()
        self_info['children'] = []
        for child in self._children:
            self_info['children'].append(child.get_debug_info())
        return self_info
