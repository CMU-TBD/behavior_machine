from behavior_machine.library.parallel_state import ParallelState
import time

from behavior_machine.core import Board, StateStatus, State, Machine, machine
from behavior_machine.library import IdleState


def test_repeat_node_in_machine_fast():

    counter = 0

    class CounterState(State):
        def execute(self, board: Board) -> StateStatus:
            nonlocal counter
            counter += 1
            return StateStatus.SUCCESS

    ds1 = CounterState("ds1")
    ds2 = CounterState("ds2")
    ds3 = CounterState("ds3")
    ds1.add_transition_on_success(ds2)
    ds2.add_transition_on_success(ds3)
    ds3.add_transition_on_success(ds1)

    exe = Machine('exe', ds1, rate=60)
    exe.start(None)
    time.sleep(2)
    exe.interrupt()
    # the performance of the computer might change this.
    assert counter >= (60 * 2) - 2
    assert counter <= (60 * 2) + 1

def test_validate_transition_immediate():

    counter = 0

    class CounterState(State):
        def execute(self, board: Board) -> StateStatus:
            nonlocal counter
            counter += 1
            return StateStatus.SUCCESS

    ds1 = CounterState("ds1")
    ds2 = CounterState("ds2")
    ds3 = CounterState("ds3")
    ds1.add_transition(lambda s, b: True, ds2)
    ds2.add_transition(lambda s, b: True, ds3)
    ds3.add_transition(lambda s, b: True, ds1)

    exe = Machine('exe', ds1, rate=60)
    exe.start(None)
    time.sleep(2)
    exe.interrupt()
    # the performance of the computer might change this.
    assert counter >= (60 * 2) - 2
    assert counter <= (60 * 2) + 1


def test_multiple_parallel_states():

    class CompleteState(State):
        def execute(self, board: Board) -> StateStatus:
            return StateStatus.SUCCESS

    num_parallel = 500
    child_states = []
    for i in range(0, num_parallel):
        child_states.append(CompleteState(f"I{i}"))

    pp = ParallelState("parallel", child_states)
    exe = Machine('exe', pp, end_state_ids=['parallel'], rate=100)
    start_time = time.time()
    exe.start(None)
    exe.wait()
    elapsed_time = time.time() - start_time
    assert elapsed_time < (1/10)

