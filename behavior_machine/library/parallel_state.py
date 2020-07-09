import threading
from ..core import StateStatus, State, NestedState
from ..board import Board
import typing
import sys


class ParallelState(NestedState):

    _children: typing.List[State]
    _thread_list: list
    _children_complete_event: threading.Event
    _child_exception: bool

    def __init__(self, name, children: list = None):
        super(ParallelState, self).__init__(name)
        self._children = [] if children is None else children
        self._children_complete_event = threading.Event()
        self._child_exception = False

    def add_children(self, state: State):
        self._children.append(state)

    def interrupt(self, timeout=None):
        # set our own flag to be true
        self._interupted_event.set()
        # send interrupt signal to all the children if they are running
        # we send the signal first to concurrenly deal with all the children
        for child in self._children:
            child._interupted_event.set()
        # we wait for each of the child to finish
        for child in self._children:
            if not child.interrupt(timeout):
                return False
        # set the complete loop
        self._children_complete_event.set()
        # we wait for the main thread to stop
        self._run_thread.join(timeout)
        return not self._run_thread.isAlive()
        # return super().interrupt(timeout=timeout)

    def execute(self, board: Board):

        # clear the event flag before starting
        self._children_complete_event.clear()
        self._child_exception = False

        # execute all the children as new threads
        for child in self._children:
            # start the children, because
            # each child starts their own thread, no extra management required
            child.start(board)

        # we delegate the checking of children state to the tick function OR execute, we wait here
        self._children_complete_event.wait()

        # if we got interupted out return INTERUPTED
        if self._interupted_event.is_set():
            return StateStatus.INTERRUPTED

        # if exception occur in one of the states
        if self._child_exception:
            # first make sure all of the states are interrupted
            for child in self._children:
                if child.checkStatus(StateStatus.RUNNING):
                    child.interrupt()
                elif child.checkStatus(StateStatus.EXCEPTIION):
                    self.propergate_exception_information(child)
            # return the exception state
            return StateStatus.EXCEPTIION

        # check the state of all the children & return success if and only if all are successful
        all_success = True
        for child in self._children:
            if not child.checkStatus(StateStatus.SUCCESS):
                all_success = False
        return StateStatus.SUCCESS if all_success else StateStatus.FAILED

    def tick(self, board):
        # check if we should transition out of this state
        next_state = super().tick(board)
        if next_state == self:
            # we are staying in this state, tick each of the child
            at_least_one_running = False
            for child in self._children:
                # if the child is running, tick it
                if child.checkStatus(StateStatus.RUNNING):
                    at_least_one_running = True
                    child.tick(board)
                elif child.checkStatus(StateStatus.FAILED):
                    self._children_complete_event.set()
                elif child.checkStatus(StateStatus.EXCEPTIION):
                    self.propergate_exception_information(child)
                    self._child_exception = True
                    self._children_complete_event.set()
            # if all child already done, we need to let the main process knows
            if not at_least_one_running:
                self._children_complete_event.set()
            # return itself since nothing transitioned
            return self
        # we are going to a new start, interrupt everthing that is going on
        if not self.interrupt():
            # we wasn't able to complete the interruption.
            # This is bad.. meaning there are bunch of zombie threads running about
            print(
                f"ERROR {self._name} of type {self.__class__} unable to complete Interrupt Action. \
                    Zombie threads likely", file=sys.stderr)
        return next_state

    def get_debug_info(self) -> typing.Dict[str, typing.Any]:

        self_info = super().get_debug_info()
        self_info['children'] = []
        for child in self._children:
            self_info['children'].append(child.get_debug_info())
        return self_info
