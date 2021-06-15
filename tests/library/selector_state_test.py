from behavior_machine.library.common_state import SetFlowState
from behavior_machine.core import Machine, State, StateStatus, Board
from behavior_machine.library import PrintState, IdleState, SelectorState


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


def test_selector_state_flow():

    class FailedState(State):
        def execute(self, board: Board) -> StateStatus:
            self.flow_out = "Failed"
            return StateStatus.FAILED

    selector = SelectorState("selector", children=[
        FailedState("failed"),
        SetFlowState("s1", "firstState"),
        SetFlowState("s2", "secondState"),
    ])
    selector.start(None)
    selector.wait()
    assert selector.flow_out == "firstState"


def test_selector_state_flow_all_failed():

    class FailedState(State):
        def execute(self, board: Board) -> StateStatus:
            self.flow_out = "Failed"
            return StateStatus.FAILED

    selector = SelectorState("selector", children=[
        FailedState("failed"),
        FailedState("failed2"),
    ])
    selector.start(None)
    selector.wait()
    assert selector.flow_out is None
