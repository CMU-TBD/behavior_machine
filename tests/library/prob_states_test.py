from behavior_machine.core import Machine, State, StateStatus, Board
from behavior_machine.library import RandomPickState


def test_random_pick():

    c1 = 0
    c2 = 0
    class s1(State):
        def execute(self, board: Board) -> StateStatus:
            nonlocal c1
            c1 += 1
            return StateStatus.SUCCESS
    class s2(State):
        def execute(self, board: Board) -> StateStatus:
            nonlocal c2
            c2 += 1
            return StateStatus.SUCCESS

    ranPick = RandomPickState(children=[
        s1(),
        s2()
    ])

    for i in range(0,1000):
        ranPick.start(None)
        ranPick.wait()
    assert 450 < c1 < 550
    assert 450 < c2 < 550
