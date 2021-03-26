import typing
import traceback
import threading

from .state_status import StateStatus
from .board import Board
from .utils import parse_debug_info

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

    def add_transition_on_complete(self, next_state: 'State') -> None:
        """Add transition to this state where when the state finishes execution regardless of output, 
        it move tos the given state.

        Parameters
        ----------
        next_state : State
            State to transition to
        """
        self.add_transition(lambda x, y: not x._run_thread.is_alive(), next_state)

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
        try:
            self.pre_execute()
            self._status = self.execute(board)
            self.post_execute()
        except Exception as e:
            self._internal_exception = e
            self._status = StateStatus.EXCEPTION
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
        if self._run_thread is not None and self._run_thread.is_alive():
            self._run_thread.join(timeout)
            return not self._run_thread.is_alive()
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

    def pre_execute(self):
        pass

    def post_execute(self):
        pass