# Changelog

## [0.4.0] - 2022-02-16
- **[Added]** `RandomPickState` which randomly pick one of the children to be executed. All children has uniform probability being picked. 
- **[Added]** added `get_status` method in `State` which return the status of the State.
- **[Changed]** name for `State` is now optional, the default is its class name.
- **[Changed]** streamlined `ParallelState` to prevent potential interrupt race issues. Enable `AtLeastOneState` to overwrite two function for its functionality.
- **[Changed]** `ParallelState` now ignores empty/None States if passed in as children.
- **[Fixed]** condition in `AtLeastOneState` where other states aren't destroyed when exiting under success condition.

## [0.3.5] - 2021-06-15
- **[Added]** `SelectorState` and `SequentialState` now has a flowout value which is from the last `succcess` state, None otherwise.
- **[Changed]** `add_transition_on_complete` now has option to not ignore exceptions (default is always not).
- **[Fixed]** race condition in `SequentialState` where the internal states are `tick()` before they are set/initialized.

## [0.3.4] - 2021-05-24
- **[Added]** Added example of the visualization on first page.
- **[Added]** `behavior_machine.visualization` which has function `visualize_behavior_machine` that can visualize any machine and it's subcomponents.
- **[Added]** Shorthand transition to transition after certain time.
- **[Added]** Examples and tests of visualization under the folder `viz_test`
- **[Fixed]** Machine now only waits for the remaining time instead of always waiting the fixed amount. Also Fixed tests with weird behavior about the waiting.
- **[Fixed]** Possible bug where Atleast returns result due to race condition.
- **[Fixed]** bug where interrupts crashs the application if called before the state starts.
- **[Fixed]** bug in test where sometimes states completed way too fast.

## [0.3.3] - 2021-05-03 
- **[Added]** `SaveFlowState`, `SetFlowFromBoardState`,`SetBoardState`,`GetBoardState` and `SetFlowState`. Three states that help with board access.
- **[Added]** Tests for the three flow access states.

## [0.3.2] - 2021-04-16
- **[Added]** `AtLeastOneState` that ends when one of its children states completes (all are run parallely) and return `success`. 

## [0.3.1] - 2021-04-15
- **[Added]** Added `SelectorState` that mimics `Selector` in behavior trees. The state run the children in order until one of them returns `success`.
- **[Added]** debugging function `get_debug_name` that returns a string with name + type to help debugging and loggin.
- **[Added]** More tests for different edge cases around transitions when reusing nodes.
- **[Changed]** `check_name` replace `checkName` and `check_status` replace `checkStatus`. The old code redirects to the new functions but throws depreciating warnings.
- **[Fixed]** linting problems throughout the program.

## [0.3.0] - 2021-04-07
- **[Added]** The **`flow`** machenism that allows you to push information from the current state directly to the next state. The variable `self.flow_in` contains the information from the previous state and you set `self.flow_out` to hold information that goes to the next state. The flow is not carried over unless specified by the state. For `machine`,`sequential states`, `flow` are passed into low-level states.
- **[Changed]** Restructure the code, such that core is in a sperate module instead of using the same file. `Board` is now in `core` instead of it's own namespace.
- **[Added]** Other tests that check for consistency of implementation.

## [0.2.4] - 2021-03-25
- **[Added]** Ability to load a python dictionary straight into the board. `board.load`
- **[Added]** A shorthand method to transition when the run_thread is done.
- **[Added]** `is_interrupted` for states to check if it is being interrupted.

## [0.2.3] - 2021-01-25
- **[Fixed]** Changed `isAlive` to `is_alive` -- by Schwarzbaer 
- **[Changed]** Change the logging framework to use the python built-in-logger.
- **[Fixed]** Typo of `EXCEPTIION`
- **[Changed]** Minor tweaks to tests.

## [0.2.2] - 2020-07-30
- **[Added]** Boards can now check if a key already exist using the `exist` method.
- **[Added]** You can specify whether a deep copy or shallow copy of an object is saved in the board using the `deep_copy` flag in the set/get methods. By default, the flag is set to true.
- **[Added]** Additional tests to check the new board functionalities and validate end state runs completely before the machine consider it complete.

## [0.2.1] - 2020-07-09
#### Added
- `get_debug_info` that returns a dict that contains debugging informations
- debug flag and callback for `Machine` that quaries all child states for information. This provide snapshot of the current states. It doesn't give the full graph due to transitions
- Tests for all those info
- Name of threads now reflect the name of the state running it. This ease debugging.

#### Changed
- Reformat the code to follow PEP8 Standard.

#### Fixed
- Bug where the `interrupt` function in the `machine` has a different method parameter than the base.
- Bug where when interrupting a machine type, nothing is returned.

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