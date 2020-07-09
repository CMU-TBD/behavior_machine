import pytest

from behavior_machine.board import Board
from behavior_machine.core import State, StateStatus, Machine


class SetState(State):

    _val: str
    _key: str

    def __init__(self, name, key, val):
        super().__init__(name)
        self._val = val
        self._key = key

    def execute(self, board):
        board.set("key", self._val)
        return StateStatus.SUCCESS


class GetState(State):

    _key: str

    def __init__(self, name, key):
        super().__init__(name)
        self._key = key

    def execute(self, board):
        value = board.get(self._key)
        board.set("output", value)
        return StateStatus.SUCCESS


class DummyState(State):
    def execute(self, board):
        return StateStatus.SUCCESS


def test_external_set_get():
    b = Board()
    b.set("x", "key1")
    assert b.get('x') == 'key1'


def test_replaced_set():
    b = Board()
    b.set("x", "hello")
    b.set("x", "world")

    assert b.get('x') == 'world'


def test_get_non_exist():
    b = Board()
    assert b.get('key') is None


def test_internal_set():
    s1 = DummyState('s1')
    set_state = SetState('set', 'key', 'hello')
    s1.add_transition_on_success(set_state)
    exe = Machine("xe", s1)
    b = Board()
    exe.start(b, manual_exec=True)
    exe.update(b, wait=True)
    assert b.get('key') == 'hello'


def test_internal_get():
    s1 = DummyState('s1')
    get_state = GetState('set', 'key')
    s1.add_transition_on_success(get_state)
    exe = Machine("xe", s1)
    b = Board()
    b.set("key", "hello_get")
    exe.start(b, manual_exec=True)
    exe.update(b, wait=True)
    assert b.get('output') == 'hello_get'
