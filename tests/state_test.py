import time
from behavior_machine.core import Board, State, StateStatus


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
    assert not t._run_thread.is_alive()


def test_is_interrupted():
    class Interruptable(State):
        def execute(self, board):
            self._interupted_event.wait()
    t = Interruptable("test")
    t.start(None)
    t.interrupt()
    assert t.is_interrupted()
    t.wait()
    assert t._status == StateStatus.NOT_SPECIFIED
    assert not t._run_thread.is_alive()


def test_exception_base(capsys):

    error_text = "error text"

    class RaiseExceptionState(State):
        def execute(self, board):
            raise IndexError(error_text)

    t = RaiseExceptionState("test_name")
    t.start(None)
    assert str(t._internal_exception) == error_text
    assert t._status == StateStatus.EXCEPTION


def test_debug_info():

    class StateName1(State):
        def execute(self, board):
            return StateStatus.SUCCESS

    s = StateName1('s1')
    info = s.get_debug_info()
    assert info.get('name') == 's1'
    assert info.get('status') == StateStatus.UNKNOWN
    assert info.get('type') == "StateName1"

def test_direct_flow():

    test_phrase = "THIS_IS_FLOW"
    test_phrase2 = "NEXT_FLOW"

    class PriorState(State):
        def execute(self, board):
            assert self.flow_in is None
            self.flow_out = test_phrase
            return StateStatus.SUCCESS

    class PostState(State):
        def execute(self, board):
            assert self.flow_in == test_phrase
            self.flow_out = test_phrase2
            return StateStatus.SUCCESS

    prior = PriorState("prior")
    post = PostState("post")
    prior.add_transition_on_success(post)
    prior.start(None)
    nextS: State = None
    while nextS is None:
        nextS = prior.tick(None)
    nextS.wait()
    assert nextS.flow_out == test_phrase2


def test_debug_name():

    class Null(State):
        def execute(self, board: Board) -> StateStatus:
            return StateStatus.SUCCESS

    n = Null("debug-test-state")
    assert n.get_debug_name() == "debug-test-state(Null)"


def test_debug_name_inherit():

    class Null(State):
        def execute(self, board: Board) -> StateStatus:
            return StateStatus.SUCCESS

    class NullX(Null):
        pass

    n = NullX("debug-test-state")
    assert n.get_debug_name() == "debug-test-state(NullX)"


def test_node_rerunning():

    counter = 0

    class Fast(State):
        def execute(self, board: Board) -> StateStatus:
            nonlocal counter
            counter += 1
            time.sleep(0.1)
            return StateStatus.SUCCESS

    f = Fast("f")
    assert f.check_status(StateStatus.UNKNOWN)
    f.start(None)
    assert f.check_status(StateStatus.RUNNING)
    f.wait()
    assert f.check_status(StateStatus.SUCCESS)
    for i in range(1, 10):
        assert counter == i
        assert f.check_status(StateStatus.SUCCESS)
        f.start(None)
        assert f.check_status(StateStatus.RUNNING)
        f.wait()
        assert f.check_status(StateStatus.SUCCESS)


def test_node_rerunning_with_connection():

    counter = 0

    class Fast(State):
        def execute(self, board: Board) -> StateStatus:
            nonlocal counter
            counter += 1
            time.sleep(0.1)
            return StateStatus.SUCCESS

    s1 = Fast("state1")
    s2 = Fast("state2")

    s1.add_transition_on_success(s2)
    s2.add_transition_on_success(s1)

    s1.start(None)
    assert s1.check_status(StateStatus.RUNNING)
    assert s2.check_status(StateStatus.UNKNOWN)
    s1.wait()
    nxt = s1.tick(None)
    assert nxt.check_status(StateStatus.RUNNING)
    assert nxt is s2
    nxt = s2.tick(None)
    assert nxt is s2
    nxt.wait()
    nxt = nxt.tick(None)
    assert nxt is s1
    assert counter == 3
    for i in range(3, 10):
        assert counter == i
        nxt.wait()
        nxt = nxt.tick(None)

def test_call_interrupt_before_start():
    class example(State):
        def execute(self, board: Board) -> StateStatus:
            return StateStatus.SUCCESS

    s = example('s')
    s.interrupt()
    
