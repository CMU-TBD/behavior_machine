import enum
from enum import Enum
import typing
import time
import sys
import traceback
import threading
from .logging import logger

from .board import Board


@enum.unique
class StateStatus(Enum):
    UNKNOWN = -1     # Unknown
    NOT_RUNNING = 0  # the default state, should be restarted by Parent after transition out
    RUNNING = 1     # The state is currently running
    SUCCESS = 2     # The state finished successfully
    FAILED = 3      # The state failed
    INTERRUPTED = 4  # Being interrupted
    EXCEPTIION = 5  # An internal uncatched exception was thrown.
    NOT_SPECIFIED = 6  # execute() didn't say


class State():

    # Name of this state
    _name: str
    _transitions: typing.Sequence[typing.Tuple[typing.Callable[[
        'State', Board], bool], 'State']]          # Store the transitions of the state
    # Hold the thread executing the action
    _run_thread: threading.Thread
    # Status of this state
    _status: StateStatus
    _internal_exception: Exception
    # Event acting as a flag for interruptions
    _interupted_event: threading.Event

    def __init__(self, name):
        self._name = name
        self._transitions = []
        self._run_thread = None
        self._interupted_event = threading.Event()
        self._internal_exception = None
        self._status = StateStatus.UNKNOWN

    def checkName(self, compare: str) -> bool:
        """Check if this state has the same name as the given state

        Parameters
        ----------
        compare : str
            Name to be checked against

        Returns
        -------
        bool
            True if the name is the same
        """
        return compare == self._name

    def checkStatus(self, compare: StateStatus) -> bool:
        """Check whether this states's status is the same as the given status

        Parameters
        ----------
        compare : StateStatus
            Enum for the status to check against

        Returns
        -------
        bool
            True if the status is the same.
        """
        return self._status == compare

    def add_transition(self, cond: typing.Callable[['State', Board], bool], next_state: 'State') -> None:
        """Add transition to the state. Provide a checking method (cond) that when returns true, will
        signal this state to transition to the state associated. Note, the transition is test in a list. If multiple
        transition function returns true, the state transition to the first added state.

        Parameters
        ----------
        cond : typing.Callable[[State, Board], bool]
            Function to determine if this transition should be taken
        next_state : State
            The next state to go to.
        """
        self._transitions.append((cond, next_state))

    def add_transition_on_success(self, next_state: 'State') -> None:
        """Add transition to this state where when it is succesfully, move to the given state.

        Parameters
        ----------
        next_state : State
            State to transition to.
        """
        self.add_transition(lambda x, y: x._status == StateStatus.SUCCESS, next_state)

    def add_transition_on_failed(self, next_state: 'State') -> None:
        """Add transition to this state where when the state fails, move to the given state.

        Parameters
        ----------
        next_state : State
            State to transition to
        """
        self.add_transition(lambda x, y: x._status == StateStatus.FAILED, next_state)

    def execute(self, board: Board) -> StateStatus:
        """All derived class should overwrite this method. It is run in a seperate thread when
        the state is running

        Parameters
        ----------
        board : Board
            Board object that is being passed between multiple states.

        Returns
        -------
        StateStatus (Optional)
            When the state completes, whether it is successful or not. This is a useful for shorthand transitions where
            state transition when successfully complete, or not.
        """
        raise NotImplementedError("Default execute method is not overwritten")

    def _execute(self, board: Board):
        # TODO Some kind of exeception catching here.
        # Right now when it fails nothing goes up
        try:
            self._status = self.execute(board)
        except Exception as e:
            self._internal_exception = e
            self._status = StateStatus.EXCEPTIION
        if self._status is None:
            self._status = StateStatus.NOT_SPECIFIED

    def start(self, board: Board) -> None:

        self._status = StateStatus.RUNNING
        self._interupted_event.clear()
        self._run_thread = threading.Thread(
            target=self._execute, args=(board,), name=self._name)
        self._run_thread.start()

    def wait(self, timeout: float = None) -> bool:
        """Wait for the current state to complete. You can also specify a timeout to prevent infinite loop

        Parameters
        ----------
        timeout : float, optional
            Timeout in seconds, None will mean wait forever, by default None

        Returns
        -------
        bool
            Whether the current state finished, if false, it means timedout.
        """
        if self._run_thread is not None and self._run_thread.isAlive():
            self._run_thread.join(timeout)
            return not self._run_thread.isAlive()
        return True

    def interrupt(self, timeout: float = None) -> bool:
        # signal the execute method to be interrupted.
        self._interupted_event.set()
        self._run_thread.join(timeout)
        # TODO check if this creates a race condition, is_alive() might still be true immediately after run() ends.
        return not self._run_thread.is_alive()

    def tick(self, board: Board) -> 'State':
        """Check whether any of the attached transitions should be taken. If yes, return the next state it should go to

        Parameters
        ----------
        board : Board
            Blackboard holding the value passed around.

        Returns
        -------
        State
            The next state if should go, self is returned if no transition should be taken.
        """
        # check all the transitions
        for transition in self._transitions:
            if transition[0](self, board):
                self.interrupt(timeout=None)
                # start the next state
                transition[1].start(board)
                return transition[1]  # return the state to the execution
        return self

    def print_debugging_info(self) -> None:
        """Print Debug Information such as name and status of state.
        """
        print(f" state name:{self._name} --- {self._status}")
        if self._internal_exception is not None:
            print(f"INTERNAL EXCEPTION {type(self._internal_exception)}")
            print(''.join(traceback.TracebackException.from_exception(
                self._internal_exception).format()))

    def get_debug_info(self) -> typing.Dict[str, typing.Any]:
        return {
            'name': self._name,
            'type': type(self).__name__,
            'status': self._status
        }


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
            self._status = self.execute(board)
        except Exception as e:
            try:
                self.interrupt()
            except RuntimeError as e2:
                if str(e2) != "cannot join current thread":
                    raise e2
                # this is a common exception because we are the current thread
                # This level of exception often happen in the transition checking level
            self._internal_exception = e
            self._status = StateStatus.EXCEPTIION
        if self._status is None:
            self._status = StateStatus.NOT_SPECIFIED

    def print_debugging_info(self):
        super().print_debugging_info()
        if self._internal_exception is not None:
            print(self._exception_raised_state_name)


class Machine(NestedState):

    _root: State  # Starting state
    _curr_state: State  # Nested state in the machine
    _started: bool  # Whether the state machine has started
    _end_state_ids: list  # IDs of end states
    _rate: float  # Rate to tick
    _debug_flag: bool
    _debug_cb: typing.Callable[[typing.Dict[str, typing.Any]], None]

    def __init__(self, name, root, end_state_ids=None, rate=1.0, debug: bool = False, debug_cb=None):
        self._root = root
        self._curr_state = root
        self._started = False
        self._end_state_ids = [] if end_state_ids is None else end_state_ids
        self._rate = 1.0 / rate
        self._debug_flag = debug
        self._debug_cb = debug_cb
        super(Machine, self).__init__(name)

    def start(self, board: Board, manual_exec=False) -> None:
        # Overwrites States' start
        # Method that is called when first enter this state.
        self._curr_state = self._root
        self._interupted_event.clear()
        # start the current state first before
        self._curr_state.start(board)
        # start the execution pipeline which automatically runs a state machine.
        if not manual_exec:
            super().start(board)

    def execute(self, board: Board):
        # tick the internal states
        while not self._interupted_event.is_set():
            time.sleep(self._rate)
            # check the internal states
            self.update(board)
            # we publish any debug information if requested
            if self._debug_flag:
                # get debug info
                debug_info = self.get_debug_info()
                # we print it to our output
                parsed_info = logger.parse_debug_info(
                    debug_info, prefix="[Base] ")
                # call the cb if we have it
                if self._debug_cb is not None:
                    self._debug_cb(debug_info, parsed_info)
                # print it
                logger.print(('\n').join(parsed_info))

            # quit if we reach an end state & the state has ended
            if self.is_end():
                return StateStatus.SUCCESS
            # check if the state or its nested states has thrown an exception
            if self._curr_state.checkStatus(StateStatus.EXCEPTIION):
                self.propergate_exception_information(self._curr_state)
                return StateStatus.EXCEPTIION
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
        return not self._curr_state._run_thread.isAlive() and \
            (self._curr_state._name == self._end_state_ids or self._curr_state._name in self._end_state_ids)

    def run(self, board: Board = None) -> None:
        """Run the machine starting from the initial/root state. This method should only be called
        from the outside of the state machine.

        Parameters
        ----------
        board : Board, optional
            Board to track variables between states, by default None
        """

        # create a board if no board is provided
        board = Board() if board is None else board

        self.start(board)
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
