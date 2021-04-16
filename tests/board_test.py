from behavior_machine.library import WaitState, IdleState
import pytest

from behavior_machine.core import Board
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


def test_board_set_deep_copy():

    b = Board()
    test_obj = {
        'hello': 'world'
    }
    b.set('obj', test_obj, deep_copy=False)
    test_obj['hello'] = 'test'
    assert b.get('obj')['hello'] == 'test'
    assert b.get('obj')['hello'] != 'world'


def test_board_get_deep_copy():

    b = Board()
    test_obj = {
        'hello': 'world'
    }
    b.set('obj', test_obj, deep_copy=False)
    rtn_obj = b.get('obj', False)
    assert rtn_obj['hello'] == 'world'
    test_obj['hello'] = 'test'
    assert rtn_obj['hello'] == 'test'


def test_board_exist_func():
    b = Board()
    b.set('hello', 'XXX')
    assert b.exist('hello')
    assert not b.exist('hello2')
    assert not b.exist('hell')


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


def test_object_set_get(capsys):

    class SetState(State):
        def execute(self, board: Board):
            obj = {
                'hello': [1, 2, 3],
                'name': {
                    'first': 'test'
                }
            }
            board.set('obj', obj)
            obj['name'] = {}
            return StateStatus.SUCCESS

    class GetState(State):
        def execute(self, board):
            obj = board.get('obj')
            assert obj['hello'] == [1, 2, 3]
            assert obj['name']['first'] == 'test'
            return StateStatus.SUCCESS

    s = SetState('s')
    g = GetState('g')
    w = WaitState('w', 1)

    s.add_transition_on_success(w)
    w.add_transition_on_success(g)
    exe = Machine('xe', s, end_state_ids=['g'])
    exe.run()
    assert exe.is_end()
    assert exe._curr_state._status == StateStatus.SUCCESS
    #assert exe._curr_state.check_status(StateStatus.SUCCESS)


def test_object_get_in_transition(capsys):

    class SetState(State):
        def execute(self, board: Board):
            obj = {
                'hello': [1, 2, 3],
                'name': {
                    'first': 'test'
                }
            }
            board.set('obj', obj)
            obj = {}
            return StateStatus.SUCCESS

    s = SetState('s')
    w = WaitState('w', 1)
    i = IdleState('i')
    end = IdleState('end')

    s.add_transition_on_success(w)
    w.add_transition_on_success(i)
    i.add_transition(lambda state, board: board.get('obj')
                     ['name']['first'] == 'test', end)
    exe = Machine('xe', s, end_state_ids=['end'])
    exe.run()
    assert exe.is_end()
    # Idle state returns RUNNING instead of SUCCESS
    assert exe._curr_state._status == StateStatus.RUNNING


def test_load_dictionary():

    b = Board()
    check_dict = {
        'k1': 'Hello',
        'k2': 800
    }
    b.load(check_dict)
    assert b.get('k1') == 'Hello'
    assert b.get('k2') == 800
    check_dict['k2'] = 100
    assert b.get('k2') == 800
    # try replacing a previous value
    check_dict_2 = {
        'k2':1000
    }
    b.load(check_dict_2)
    assert b.get('k2') == 1000

