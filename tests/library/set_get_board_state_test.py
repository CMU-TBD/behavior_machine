from behavior_machine.core import Board
from behavior_machine.library import GetBoardState, SetBoardState

def test_set_board_state():

    b = Board() 
    assert b.get("test_key") is None
    set_board = SetBoardState("set", "test_key", "hello")
    set_board.start(b)
    set_board.wait()
    assert b.get("test_key") == "hello"
    assert b.get("test_key")

def test_get_board_state():

    b = Board()
    b.set("other_key", 10001)
    get_board = GetBoardState("get", "other_key")
    get_board.start(b)
    get_board.wait()
    assert get_board.flow_out == 10001