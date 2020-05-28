# Changelog


## [0.2.0] - 2020-05-27
#### Added
- API to print debugging information.
- More docstrings for common methods.
- Interruption handling in both parallel and sequential states. Included test for them
- Tested performance of the system
- new status called `NOT_SPECIFIED` for cases where no status is returned.
- README and basic example

#### Changed
- Changed `interupted` from a boolean to `threading.Event` allow easy cross thread timeout.
- `WaitState` now immediately stops when wait timedout instead of relying on a polling at 10Hz.
- Added class decerator for Enum to make sure `StateStatus` has unique numbers.
- Renamed package to `behavior_machine` & StandardStateLibrary to just `library`

#### Fixed
- Bug where `StateStatus.UNKNOWN` and `StateStatus.INTERRUPTED` had the same number.
- Bug where threads were not cleaned up when transitioned out of parallel and sequential.
- Race condition in Sequential State where when the Sequential State gets transitioned out, the child thread was asked to join before initialized.
- Exception when checking transitions is now handled correctly and call interupts for internal states.

## [0.1.0] - 2020-05-19
#### Added
- ability to timeout for state & tests for it.
- method to add transition when the state failed.
- `ParallelState` that runs all the children simultanously.
- Catch-all exception checking in `execute`. All exceptions are now handled and slowly bubble up to the highest state with information saved in `_inner_exception`.
- Added multiple test for exception handling
- `WaitState` could now be interrupted and end early.
- `NestedState` object that derives from `State`. This object allows sharing of functions that are used in nested scenarios.

#### Changed
- Change some test to use pytest methods.
- `SequentialMachine` is renamed to `SequentialState`
- All states that have nested states are now derived from `NestedState`

## [0.0.4] - 2020-04-28
#### Added
- `WaitState` that waits for X seconds before continuing, and its corresponding tests.

#### Changed
- Switched testing from `unittest` to `pytest`

#### Fixed
- Exception when no `endStates` are passed into a state machine's constructor.

## [0.0.3] - 2020-04-06
    - Changed unittest from `setuptools` to `tox`.
    - Added more unit test
    - Renamed `ExecutionMachine` to `Machine`
## [0.0.2]
    - Split out classes in state into their seperate files.
    - Fixed bug where `run` creates two initial states.
    - added StandardStateLibrary with `print state`, `sequential machine`.
## [0.0.1]
    Initial Construct