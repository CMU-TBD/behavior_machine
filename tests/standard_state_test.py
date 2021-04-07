import time
import sys
import io
import pytest

from behavior_machine.core import Board
from behavior_machine.core import State, StateStatus, Machine
from behavior_machine.library import WaitState, IdleState, PrintState


def test_print_state(capsys):

    print_text = "this is a print_text"
    ps = PrintState("p1", print_text)
    es = IdleState("endState")
    ps.add_transition_on_success(es)
    exe = Machine("xe", ps, end_state_ids=["endState"], rate=10)
    exe.run()
    captured = capsys.readouterr()
    assert captured.out == print_text + '\n'


def test_wait_state():

    s1 = WaitState("s1", 2)
    s2 = IdleState("s2")
    s1.add_transition_on_success(s2)

    exe = Machine("test", s1, end_state_ids=['s2'], rate=10)

    start_time = time.time()
    exe.run()
    duration = time.time() - start_time
    # Because the waut these are executed, its hard to know the margin
    assert duration == pytest.approx(2, rel=0.1)


def test_wait_state_with_interrupt():

    s1 = WaitState("s1", 10)
    start_time = time.time()
    s1.start(None)
    s1.interrupt()
    s1.wait()
    duration = time.time() - start_time
    # Because the waut these are executed, its hard to know the margin
    # should be really close to zero because we interrupt immediately after it started.
    assert duration == pytest.approx(0.0, abs=1e-3)
