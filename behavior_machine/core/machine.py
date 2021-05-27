import logging
import sys
import time
import typing

from .board import Board
from .nested_state import NestedState
from .state import State, StateStatus
from .utils import parse_debug_info


class Machine(NestedState):

    _root: State  # Starting state
    _curr_state: State  # Nested state in the machine
    _started: bool  # Whether the state machine has started
    _end_state_ids: list  # IDs of end states
    _rate: float  # Rate to tick
    _debug_flag: bool
    _debug_cb: typing.Callable[[typing.Dict[str, typing.Any]], None]
    _logger: logging.Logger

    def __init__(self, name, root, end_state_ids=None, rate=1.0, debug: bool = False, debug_cb=None, logger: logging.Logger = None):
        self._root = root
        self._curr_state = root
        self._started = False
        self._end_state_ids = [] if end_state_ids is None else end_state_ids
        self._rate = 1.0 / rate
        self._debug_flag = debug
        self._debug_cb = debug_cb
        self._logger = logger
        super(Machine, self).__init__(name)

    def start(self, board: Board, flow_in: typing.Any = None, manual_exec=False) -> None:
        # Overwrites States' start
        self._status = StateStatus.RUNNING
        # Method that is called when first enter this state.
        self._curr_state = self._root
        self._interupted_event.clear()
        # start the current state first before
        self._curr_state.start(board, flow_in)
        # start the execution pipeline which automatically runs a state machine.
        if not manual_exec:
            super().start(board)

    def execute(self, board: Board):
        # tick the internal states
        while not self.is_interrupted():
            # start time
            start_time_tick = time.time()
            # check the internal states
            self.update(board)
            # we publish any debug information if requested
            if self._debug_flag:
                # get debug info
                debug_info = self.get_debug_info()
                # parse the information
                parsed_info = parse_debug_info(debug_info, prefix="[Base] ")
                # call the cb if we have it
                if self._debug_cb is not None:
                    self._debug_cb(debug_info, parsed_info)
                # log it
                if self._logger is not None:
                    self._logger.debug(('\n').join(parsed_info))

            # quit if we reach an end state & the state has ended
            if self.is_end():
                return StateStatus.SUCCESS
            # check if the state or its nested states has thrown an exception
            if self._curr_state.check_status(StateStatus.EXCEPTION):
                self.propergate_exception_information(self._curr_state)
                return StateStatus.EXCEPTION

            #TODO this part probably can be improved through better code + CPYTHON implementaions
            # sleep for the remaining time
            passed_time = time.time() - start_time_tick
            if passed_time > self._rate:
                # warn about slow tick rate
                if self._logger is not None:
                    self._logger.warn(f"Machine{self.get_debug_name()} \
                        ticking at {passed_time} which is larger than {self._rate}")
            else:
                time.sleep(self._rate - passed_time)

        return StateStatus.INTERRUPTED

    def tick(self, board: Board) -> State:
        # Overwrites State's tick
        # Because this is machine, when it is interrupted, it interrupt its lower level entities first.
        for transition in self._transitions:
            if transition[0](self, board):
                # this means this machine is being transitioned out.
                # tell the current state to stop.
                self._curr_state.interrupt()
                self.interrupt()
                transition[1].start(board)
                return transition[1]
        return self

    def update(self, board: Board, wait=False) -> None:
        """ Check if the current state should transition. If wait is set to True, also wait for
        the current state to complete. Note, the wait is mostly use for testing.

        Parameters
        ----------
        board : Board
            Board to pass information between states.
        wait : bool, optional
            Whether to wait for current state to complete, by default False
        """
        if wait:
            self._curr_state.wait()
        self._curr_state = self._curr_state.tick(board)

    def is_end(self) -> bool:
        return not self._curr_state._run_thread.is_alive() and \
            (self._curr_state._name == self._end_state_ids or self._curr_state._name in self._end_state_ids)

    def run(self, board: Board = None, flow_in: typing.Any = None) -> None:
        """Run the machine starting from the initial/root state. This method should only be called
        from the outside of the state machine.

        Parameters
        ----------
        board : Board, optional
            Board to track variables between states, by default None
        flow_in : Any, optional
            Data that is initially passed to the root state to help execution.
        """

        # create a board if no board is provided
        board = Board() if board is None else board

        self.start(board, flow_in)
        self.wait()

    def interrupt(self, timeout: float = None) -> bool:
        # call interrupt for the nested class
        if not self._curr_state.interrupt(timeout):
            # unable to interrupt current state
            print(
                f"ERROR {self._name} of type {self.__class__} unable to complete Interrupt Action. \
                    Zombie threads likely", file=sys.stderr)
            return False
        return super().interrupt(timeout)

    def get_debug_info(self) -> typing.Dict[str, typing.Any]:

        self_info = super().get_debug_info()
        self_info['children'] = [self._curr_state.get_debug_info()]
        return self_info
