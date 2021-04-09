import time
import sys
import io
import pytest

from behavior_machine.core import Machine, State, StateStatus, Board, state_status
from behavior_machine.library import SequentialState, PrintState, IdleState, WaitState, SelectorState


def test_selector_state(capsys):

    class FailState(State):

        def execute(self, board: Board) -> StateStatus:
            print("failed1")
            return StateStatus.FAILED

    fs1 = FailState("fs")
    ps1 = PrintState("ps1", "Print1")
    ps2 = PrintState("ps2", "Print2")
    ps3 = PrintState("ps3", "Print3")
    es = IdleState("endState")

    sm = SelectorState("ss", children=[fs1, ps2, ps3])
    sm.add_children(ps1)

    sm.add_transition_on_success(es)
    exe = Machine("xe", sm, end_state_ids=["endState"], rate=10)
    exe.run()

    assert capsys.readouterr().out == "failed1\nPrint2\n"

def test_selector_state_all_failed():

    class FailState(State):
        def execute(self, board: Board) -> StateStatus:
            return StateStatus.FAILED
    
    fs1 = FailState("f1")
    fs2 = FailState("f2")
    fs3 = FailState("f3")
    es = IdleState("endState")

    sm = SelectorState("ss", children=[fs1, fs2, fs3])
    sm.add_transition_on_failed(es)

    exe = Machine("exe", sm, end_state_ids=['endState'], rate=10)
    exe.run()

    assert fs1.check_status(StateStatus.FAILED)
    assert fs2.check_status(StateStatus.FAILED)
    assert fs3.check_status(StateStatus.FAILED)
    assert sm.check_status(StateStatus.FAILED)