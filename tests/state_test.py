import pytest
import sys
import io
import time

from behavior_machine.board import Board
from behavior_machine.core import State, StateStatus, Machine


def test_state_timeout(capsys):

    class WaitState(State):
        def execute(self, board):
            time.sleep(2)
            return StateStatus.SUCCESS

    t1 = WaitState("test")
    t1.start(None)
    assert not t1.wait(1)
    assert t1.wait(1.1)


def test_interrupt_timeout():
    class WaitState(State):
        def execute(self, board):
            time.sleep(2)
            return StateStatus.SUCCESS

    t1 = WaitState("test")
    t1.start(None)
    assert not t1.interrupt(timeout=0.01)


def test_interrupt():
    class Interruptable(State):
        def execute(self, board):
            self._interupted_event.wait()
    t = Interruptable("test")
    t.start(None)
    t.interrupt()
    t.wait()
    assert t._status == StateStatus.NOT_SPECIFIED
    assert not t._run_thread.isAlive()


def test_exception_base(capsys):

    error_text = "error text"

    class RaiseExceptionState(State):
        def execute(self, board):
            raise IndexError(error_text)

    t = RaiseExceptionState("test_name")
    t.start(None)
    assert str(t._internal_exception) == error_text
    assert t._status == StateStatus.EXCEPTIION


def test_debug_info():

    class StateName1(State):
        def execute(self, board):
            return StateStatus.SUCCESS

    s = StateName1('s1')
    info = s.get_debug_info()
    assert info.get('name') == 's1'
    assert info.get('status') == StateStatus.UNKNOWN
    assert info.get('type') == "StateName1"
