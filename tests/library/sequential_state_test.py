import time
import sys
import io
import pytest

from behavior_machine.board import Board
from behavior_machine.core import Machine, State, StateStatus
from behavior_machine.library import SequentialState, PrintState, IdleState, WaitState


def test_sequential_state(capsys):

    ps1 = PrintState("ps1", "Print1")
    ps2 = PrintState("ps1", "Print2")
    ps3 = PrintState("ps1", "Print3")
    es = IdleState("endState")

    sm = SequentialState("sm", children=[ps2, ps3])
    sm.add_children(ps1)

    sm.add_transition_on_success(es)
    exe = Machine("xe", sm, end_state_ids=["endState"], rate=10)
    exe.run()

    assert capsys.readouterr().out == "Print2\nPrint3\nPrint1\n"


def test_nested_sequential_state(capsys):
    ps1 = PrintState("ps1", "Print1")
    ps2 = PrintState("ps2", "Print2")
    ps3 = PrintState("ps3", "Print3")
    ps4 = PrintState("ps4", "Print4")
    es = IdleState("endState")

    sm = SequentialState("sm", children=[ps3, ps2])
    sm2 = SequentialState("sm2", children=[ps4, sm, ps1])
    sm2.add_transition_on_success(es)
    mach = Machine("xe", sm2, end_state_ids=['endState'], rate=10)
    mach.run()

    assert capsys.readouterr().out == "Print4\nPrint3\nPrint2\nPrint1\n"


def test_exception_in_sequential_state(capsys):

    error_text = "IndexErrorInTestEXCEPTION"

    class RaiseExceptionState(State):
        def execute(self, board):
            raise IndexError(error_text)

    ps1 = PrintState("ps1", "Print1")
    ps2 = PrintState("ps1", "Print2")
    ps3 = PrintState("ps1", "Print3")
    rs = RaiseExceptionState("rs1")
    es = IdleState("endState")

    sm = SequentialState("sm", children=[ps2, ps3, rs])
    sm.add_children(ps1)

    sm.add_transition_on_success(es)
    exe = Machine("xe", sm, end_state_ids=["endState"])
    exe.run()

    assert capsys.readouterr().out == "Print2\nPrint3\n"
    assert str(exe._internal_exception) == error_text
    assert exe._exception_raised_state_name == "xe.sm.rs1"


def test_interruption_in_sequential_state(capsys):

    ws1 = WaitState("ws1", 0.1)
    ws2 = WaitState("ws2", 0.1)
    ps1 = PrintState("ps1", "Print1")

    sm = SequentialState("sm", children=[ws1, ws2, ps1])
    sm.start(None)
    sm.wait(0.15)
    sm.interrupt()

    assert capsys.readouterr().out == ""
    assert sm.checkStatus(StateStatus.INTERRUPTED)
    assert ws2.checkStatus(StateStatus.INTERRUPTED)
    assert ws1.checkStatus(StateStatus.SUCCESS)
    assert ps1.checkStatus(StateStatus.UNKNOWN)
    assert not sm._run_thread.isAlive()
    assert not ws1._run_thread.isAlive()
    assert not ws2._run_thread.isAlive()


def test_sequential_state_success(capsys):
    ps1 = PrintState("ps1", "Print1")
    ps2 = PrintState("ps2", "Print2")
    es = IdleState("es")
    seqs = SequentialState("sm", children=[ps1, ps2])
    seqs.add_transition_on_success(es)
    exe = Machine("m1", seqs, ['es'])
    exe.run()

    assert capsys.readouterr().out == "Print1\nPrint2\n"
    assert exe.is_end()
    assert exe._curr_state == es
    assert seqs._status == StateStatus.SUCCESS
    assert ps1._status == StateStatus.SUCCESS
    assert ps2._status == StateStatus.SUCCESS


def test_interruption_in_machines_with_sequential_state(capsys):

    ws1 = WaitState("ws1", 0.2)
    ws2 = WaitState("ws2", 0.2)
    ps1 = PrintState("ps1", "Print1")
    es = IdleState("es")
    iss = IdleState("iss")
    sm = SequentialState("sm", children=[ws1, ws2, ps1])
    sm.add_transition_on_success(es)
    sm.add_transition(lambda s, b: s._curr_child.checkName('ws2'), iss)

    exe = Machine("exe", sm, ["es", "iss"], rate=100)
    exe.run()
    assert exe._exception_raised_state_name == ""
    assert exe._internal_exception is None
    assert exe._status == StateStatus.SUCCESS
    assert not exe._run_thread.isAlive()
    assert exe._curr_state._name == 'iss'
    assert exe.is_end()
    assert capsys.readouterr().out == ""
    assert not sm._run_thread.isAlive()
    assert not ws1._run_thread.isAlive()
    assert not ws2._run_thread.isAlive()
    assert sm._status == StateStatus.INTERRUPTED
    assert ws2._status == StateStatus.INTERRUPTED
    assert ws1._status == StateStatus.SUCCESS
    assert ps1._status == StateStatus.UNKNOWN
    assert ws2.checkStatus(StateStatus.INTERRUPTED)
    assert ws1.checkStatus(StateStatus.SUCCESS)


def test_sequential_debug_info():
    w1 = WaitState('w1', 1)
    w2 = WaitState('w2', 1)
    seqs = SequentialState('seqs', [w1, w2])
    seqs.start(None)
    seqs.wait(0.1)
    info = seqs.get_debug_info()
    assert info['name'] == 'seqs'
    assert len(info['children']) == 2
    assert info['children'][0]['name'] == 'w1'
    assert info['children'][0]['status'] == StateStatus.RUNNING
    assert info['children'][1]['name'] == 'w2'
    assert info['children'][1]['status'] == StateStatus.UNKNOWN
    seqs.wait(1)
    info = seqs.get_debug_info()
    assert info['children'][0]['status'] == StateStatus.SUCCESS
    assert info['children'][1]['status'] == StateStatus.RUNNING
    seqs.wait()
