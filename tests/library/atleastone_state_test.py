import time
import sys
import io
import pytest
import typing

from behavior_machine.core import Machine, State, StateStatus, Board
from behavior_machine.library import PrintState, AtLeastOneState, SequentialState, IdleState, WaitState


def test_atleastone_state(capsys):

    ps1 = PrintState('p1', "ps1")
    ws1 = WaitState("w1", 0.5)
    ps2 = PrintState('p2', "ps2")

    one = AtLeastOneState("one", children=[
        ps2,
        SequentialState("seq", children=[
            ws1,
            ps1
        ])
    ])
    es = IdleState("endState")
    one.add_transition_on_success(es)
    exe = Machine("xe", one, end_state_ids=["endState"], rate=10)
    exe.run()

    assert capsys.readouterr().out == "ps2\n"


def test_atleastone_interrupt(capsys):

    interrupted = False

    class WaitAndPrint(State):
        def execute(self, board: Board) -> typing.Optional[StateStatus]:
            time.sleep(0.5)
            if self.is_interrupted():
                nonlocal interrupted
                interrupted = True
                return StateStatus.INTERRUPTED
            print("HelloWorld")
            return StateStatus.SUCCESS

    one = AtLeastOneState("one", children=[
        PrintState('p5', "ps5"),
        WaitAndPrint("ws")
    ])
    es = IdleState("endState")
    one.add_transition_on_success(es)
    exe = Machine("xe", one, end_state_ids=["endState"], rate=10)
    exe.run()

    assert capsys.readouterr().out == "ps5\n"
    assert interrupted


def test_checking_too_fast():

    class SuccessState(State):

        def execute(self, board: Board) -> StateStatus:
            time.sleep(1)
            return StateStatus.SUCCESS
        

    one = AtLeastOneState("one", children=[
        SuccessState("is1"),
        SuccessState("is2"),
    ])
    exe = Machine("xe", one, end_state_ids=["one"], rate=500)
    exe.tick(None)
    exe.run(None)

    assert one._status == StateStatus.SUCCESS

