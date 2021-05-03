import time
import sys
import io
import pytest

from behavior_machine.core import Board
from behavior_machine.core import State, Machine, StateStatus
from behavior_machine.library import SaveFlowState, SetFlowFromBoardState, SetFlowState, IdleState


def test_set_flow_state():

    test_value = 1001

    sf = SetFlowState("s1", test_value)
    id = IdleState('id')
    sf.add_transition_on_success(id)
    sf.start(None)
    sf.wait()
    nxt = sf.tick(None)
    assert nxt == id
    assert id.flow_in == test_value


def test_set_flow_state_deep_copy():

    test_value = {
        'value':100
    }

    sf = SetFlowState("s1", test_value)
    test_value['value'] = 200
    id = IdleState('id')
    sf.add_transition_on_success(id)
    sf.start(None)
    sf.wait()
    nxt = sf.tick(None)
    assert nxt == id
    assert nxt.flow_in['value'] != test_value['value']
    assert nxt.flow_in['value'] == 100

    sf2 = SetFlowState("s2", test_value, deep_copy=False)
    test_value['value'] = 300
    sf2.add_transition_on_success(id)
    sf2.start(None)
    sf2.wait()
    nxt = sf2.tick(None)
    assert nxt == id
    assert nxt.flow_in['value'] == test_value['value']
    assert nxt.flow_in['value'] != 200

def test_save_flow_state():

    test_val = "test_save_flow_23435"
    sf = SaveFlowState("sf", "save_to_loc")
    b = Board()
    sf.start(b,test_val)
    sf.wait()
    assert b.get("save_to_loc") == test_val

def test_set_flow_from_board():

    test_val = "test_set_flow_from_board_23421353"
    b = Board()
    b.set("loc_to_get", test_val)
    sfb = SetFlowFromBoardState("sfb","loc_to_get")
    ist = IdleState("ist")
    sfb.add_transition_on_success(ist)
    sfb.start(b)
    sfb.wait()
    sfb.tick(b)
    assert sfb.flow_out == test_val
    assert ist.flow_in == test_val

