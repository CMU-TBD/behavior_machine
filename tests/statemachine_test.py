from behavior_machine.library import WaitState
import pytest
import sys
import io
import time

from behavior_machine.board import Board
from behavior_machine.core import State, StateStatus, Machine


class PrintState(State):

    _text: str

    def __init__(self, name, text):
        super().__init__(name)
        self._text = text

    def execute(self, board):
        print(self._text)
        return StateStatus.SUCCESS


class DummyState(State):
    def execute(self, board):
        return StateStatus.SUCCESS


def test_simple_machine(capsys):
    ps1 = PrintState("ps1", "print1")
    ps2 = PrintState("ps2", "print2")
    ps1.add_transition_on_success(ps2)
    exe = Machine("xe", ps1, end_state_ids=["ps2"], rate=10)
    b = Board()
    exe.run(b)
    assert exe.is_end()
    assert capsys.readouterr().out == "print1\nprint2\n"


def test_transition_on_failed(capsys):

    class failedState(State):
        def execute(self, board):
            return StateStatus.FAILED

    fs = failedState('fs')
    ps1 = PrintState("ps1", "success")
    ps2 = PrintState("ps2", "failed")
    fs.add_transition_on_success(ps1)
    fs.add_transition_on_failed(ps2)
    exe = Machine("xe", fs, end_state_ids=["ps1", "ps2"], rate=10)
    exe.run(None)
    assert exe.is_end()
    assert exe._curr_state.checkName("ps2")
    assert capsys.readouterr().out == "failed\n"


def test_simple_machine2(capsys):
    ps1 = PrintState("ps1", "print1")
    ps2 = PrintState("ps2", "print2")
    ps3 = PrintState("ps3", "print3")
    ps1.add_transition_on_success(ps2)
    ps2.add_transition_on_success(ps3)
    exe = Machine("xe", ps1, rate=10)
    b = Board()
    exe.start(b, manual_exec=True)
    assert capsys.readouterr().out == "print1\n"
    exe.update(b, wait=True)
    assert capsys.readouterr().out == "print2\n"
    exe.update(b, wait=True)
    assert capsys.readouterr().out == "print3\n"


def test_chain_case():
    s1 = DummyState("s1")
    s2 = DummyState("s2")
    s1.add_transition_on_success(s2)
    s3 = DummyState("s3")
    s2.add_transition_on_success(s3)
    exe = Machine("xe", s1, end_state_ids=["s3"], rate=10)
    b = Board()
    exe.start(b, manual_exec=True)
    exe.update(b, True)
    assert not exe.is_end()
    exe.update(b, True)
    assert exe.is_end()


def test_end_case():
    ps1 = PrintState("ps1", "Hello World")
    es = DummyState("endState")
    ps1.add_transition_on_success(es)
    exe = Machine("xe", ps1, end_state_ids=["endState"], rate=10)
    exe.run()
    assert exe.is_end()


def test_machine_rate_slow():
    ps1 = PrintState("ps1", "print1")  # execute at second 0
    ps2 = PrintState("ps1", "print2")  # execute at second 2
    es = DummyState("endState")  # execute at second 4
    ps1.add_transition_on_success(ps2)
    ps2.add_transition_on_success(es)
    exe = Machine("xe", ps1, end_state_ids=["endState"], rate=0.5)
    start_time = time.time()
    exe.run()
    duration = time.time() - start_time
    assert 4 == pytest.approx(duration, rel=1e-2)


def test_machine_rate_fast():
    ps1 = PrintState("ps1", "print1")  # execute at second 0
    ps2 = PrintState("ps1", "print2")  # execute at second 0.1
    es = DummyState("endState")  # execute at second 0.2
    ps1.add_transition_on_success(ps2)
    ps2.add_transition_on_success(es)
    exe = Machine("xe", ps1, end_state_ids=["endState"], rate=10)
    start_time = time.time()
    exe.run()
    duration = time.time() - start_time
    assert 0.2 == pytest.approx(duration, abs=1e-2)


def test_nested_machine(capsys):

    ps1 = PrintState("ps1", "in mach1")
    ps15 = PrintState("ps15", "in mach1 too")
    es = DummyState("endState")
    ps1.add_transition_on_success(ps15)
    ps15.add_transition_on_success(es)
    mach1 = Machine("xe", ps1, end_state_ids=["endState"], rate=10)

    ps2 = PrintState("ps2", "enter mach1")
    ps2.add_transition_on_success(mach1)
    ps3 = PrintState("ps3", "leaving mach1")
    mach1.add_transition_on_success(ps3)
    es2 = DummyState("endState")
    ps3.add_transition_on_success(es2)

    mac2 = Machine("mac2", ps2, end_state_ids=["endState"], rate=10)
    mac2.run()

    assert capsys.readouterr().out == "enter mach1\nin mach1\nin mach1 too\nleaving mach1\n"


class RaiseExceptionState(State):

    def execute(self, board):
        raise InterruptedError("raiseException")


def test_machine_with_exception(capsys):

    ps1 = PrintState("ps1", "p1")
    re1 = RaiseExceptionState('re1')
    ps2 = PrintState("ps2", "p2")

    ps1.add_transition_on_success(re1)
    re1.add_transition_on_success(ps2)

    mac = Machine("mac", ps1, ["ps2"])
    mac.run()

    assert capsys.readouterr().out == 'p1\n'
    assert mac.checkStatus(StateStatus.EXCEPTIION)
    assert str(mac._internal_exception) == "raiseException"
    assert mac._exception_raised_state_name == "mac.re1"


def test_machine_with_exception_in_transition(capsys):

    is1 = DummyState('d1')
    is2 = DummyState('d2')

    is1.add_transition(lambda s, b: s.unknown(), is2)

    mac = Machine("mac", is1, ["is2"])
    mac.run()

    assert mac._status == StateStatus.EXCEPTIION
    assert not mac._run_thread.isAlive()
    assert not is1._run_thread.isAlive()
    assert is2._run_thread is None  # Never reach is2


def test_machine_with_exception_in_transition_with_zombie_states(capsys):

    ws1 = WaitState('ws1', 10)
    is2 = DummyState('d2')

    ws1.add_transition(lambda s, b: s.unknown(), is2)

    mac = Machine("mac", ws1, ["is2"])
    mac.run()
    assert mac._status == StateStatus.EXCEPTIION
    # this is an interrupted, because exception happen at higher level
    assert ws1._status == StateStatus.INTERRUPTED
    assert not mac._run_thread.isAlive()
    assert not ws1._run_thread.isAlive()
    assert is2._run_thread is None  # Never reach it


def test_debugging_machine(capsys):

    from behavior_machine import logging
    logging.add_fs('capsys', sys.stdout)
    s1 = WaitState('s1', 1.1)
    s2 = DummyState('s2')
    s1.add_transition_on_success(s2)
    mac = Machine("mac", s1, ["s2"], debug=True, rate=1)
    mac.run()
    assert mac.is_end()
    assert capsys.readouterr().out == ("[Base] mac(Machine) -- RUNNING\n"
                                       "  -> s1(WaitState) -- RUNNING\n"
                                       "[Base] mac(Machine) -- RUNNING\n"
                                       "  -> s2(DummyState) -- SUCCESS\n")


def test_interrupt_machine(capsys):
    s1 = WaitState('s1', 1.1)
    s2 = DummyState('s2')
    s1.add_transition_on_success(s2)
    mac = Machine("mac", s1, ["s2"], debug=True, rate=1)
    mac.start(None)
    assert mac.interrupt()
