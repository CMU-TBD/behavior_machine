import time
import sys
import io
import pytest

from behavior_machine.core import Board
from behavior_machine.core import State, Machine, StateStatus
from behavior_machine.library import WaitState, ParallelState, IdleState


def test_parallel_state_individual(capsys):

    ws = WaitState("ws1", 1)
    ws2 = WaitState("ws2", 2)

    pm = ParallelState('pm', [ws, ws2])

    pm.start(None)
    # wait for one second outside
    time.sleep(1)
    pm.tick(None)  # ticks to force event flags if any
    assert not pm.wait(0.1)
    assert pm.check_status(StateStatus.RUNNING)
    # at this point ws should be done but ws2 is still going
    time.sleep(1.1)
    pm.tick(None)  # ticks to force event flags if any
    # wait
    assert pm.wait(0.1)
    assert not pm.check_status(StateStatus.RUNNING)
    assert pm.check_status(StateStatus.SUCCESS)
    assert not pm._run_thread.is_alive()


def test_parallel_state_in_machine(capsys):
    ws = WaitState("ws1", 1)
    ws2 = WaitState("ws2", 2)
    es = IdleState("es")
    pm = ParallelState('pm', [ws, ws2])
    pm.add_transition_on_success(es)
    exe = Machine("main_machine", pm, end_state_ids=['es'], rate=10)
    # run machine and see how it reacts
    exe.start(None)
    # wait for one second
    assert not exe.wait(1.1)
    assert ws.check_status(StateStatus.SUCCESS)
    assert ws2.check_status(StateStatus.RUNNING)
    assert exe.check_status(StateStatus.RUNNING)
    # at this point ws should be done but ws2 is still going
    # wait another one seconds
    assert exe.wait(2)
    assert exe.check_status(StateStatus.SUCCESS)
    assert not pm._run_thread.is_alive()


def test_parallel_one_state_fails(capsys):

    class FailAfter1SecState(State):
        def execute(self, board):
            time.sleep(1)
            return StateStatus.FAILED

    ws = WaitState("ws1", 5)
    fs = FailAfter1SecState("fs")
    es = IdleState("es")
    fes = IdleState("fs-terminal")
    pm = ParallelState('pm', [ws, fs])
    pm.add_transition_on_success(es)
    pm.add_transition_on_failed(fes)
    exe = Machine("main_machine", pm, end_state_ids=[
                  'es', 'fs-terminal'], rate=10)

    # run machine and see how it reacts
    exe.start(None)
    # wait for one second
    assert not exe.wait(0.5)
    assert exe.check_status(StateStatus.RUNNING)
    assert exe._curr_state.check_name('pm')
    # at this point ws should be done but ws2 is still going
    # wait another one seconds
    assert exe.wait(2)
    assert exe._curr_state == fes
    assert not pm._run_thread.is_alive()

def test_parallel_one_state_exception(capsys):

    class ExceptionAfter1SecState(State):
        def execute(self, board):
            time.sleep(1)
            return StateStatus.EXCEPTION

    ws = WaitState("ws1", 5)
    fs = ExceptionAfter1SecState("fs")
    es = IdleState("es")
    fes = IdleState("fs-terminal")
    pm = ParallelState('pm', [ws, fs])
    pm.add_transition_on_success(es)
    pm.add_transition_on_failed(fes)
    exe = Machine("main_machine", pm, end_state_ids=[
                  'es', 'fs-terminal'], rate=10)

    # run machine and see how it reacts
    exe.start(None)
    # wait for 0.5 second to see it is still running
    assert not exe.wait(0.5)
    assert exe.check_status(StateStatus.RUNNING)
    assert exe._curr_state.check_name('pm')
    # at this point, it should throw or raise the exception
    # wait another 1.5 seconds
    assert exe.wait(1.5)
    assert exe.check_status(StateStatus.EXCEPTION)
    assert not pm._run_thread.is_alive()

def test_parallel_one_state_throw_exception(capsys):

    class ExceptionAfter1SecState(State):
        def execute(self, board):
            time.sleep(1)
            raise Exception("test exception")
            #return StateStatus.EXCEPTION

    ws = WaitState("ws1", 5)
    fs = ExceptionAfter1SecState("fs")
    es = IdleState("es")
    fes = IdleState("fs-terminal")
    pm = ParallelState('pm', [ws, fs])
    pm.add_transition_on_success(es)
    pm.add_transition_on_failed(fes)
    exe = Machine("main_machine", pm, end_state_ids=[
                  'es', 'fs-terminal'], rate=10)

    # run machine and see how it reacts
    exe.start(None)
    # wait for 0.5 second to see it is still running
    assert not exe.wait(0.5)
    assert exe.check_status(StateStatus.RUNNING)
    assert exe._curr_state.check_name('pm')
    # at this point, it should throw or raise the exception
    # wait another 1.5 seconds
    assert exe.wait(1.5)
    assert exe.check_status(StateStatus.EXCEPTION)
    assert not pm._run_thread.is_alive()


def test_exception_in_parallel_state(capsys):

    error_text = "IndexErrorInTestEXCEPTION"

    class RaiseExceptionState(State):
        def execute(self, board):
            raise IndexError(error_text)

    ws = WaitState("ws1", 10)
    re = RaiseExceptionState("re")
    pm = ParallelState('pm', [ws, re])
    es = IdleState("es")
    pm.add_transition_on_success(es)
    exe = Machine("xe", pm, end_state_ids=['es', 'onException'], rate=10)
    # run machine and see how it reacted
    exe.start(None)
    exe.wait(0.5)
    assert exe._curr_state == pm
    assert exe.check_status(StateStatus.EXCEPTION)
    assert str(exe._internal_exception) == error_text
    assert exe._exception_raised_state_name == "xe.pm.re"
    assert not pm._run_thread.is_alive()


def test_interrupt_in_parallel_state(capsys):
    ws = WaitState("ws1", 1)
    ws2 = WaitState("ws2", 2)
    es = IdleState("es")
    pm = ParallelState('pm', [ws, ws2])
    pm.add_transition_on_success(es)
    pm.add_transition_after_elapsed(es, 0.1)
    exe = Machine("main_machine", pm, end_state_ids=['es'], rate=10)
    # run machine
    exe.start(None)
    # because of the elapsed transition, the machine will immediate transition to the end state in 0.1 seconds
    assert exe.wait(0.2)
    assert ws._status == StateStatus.INTERRUPTED
    assert ws2._status == StateStatus.INTERRUPTED
    assert not pm._run_thread.is_alive()

def test_parallel_state_performance(capsys):

    wait_state_list = []
    for i in range(0, 1000):
        wait_state_list.append(WaitState(f"wait{i}", 1))

    pm = ParallelState('pm', wait_state_list)
    exe = Machine("xe", pm, rate=10)
    start_time = time.time()
    exe.start(None)
    pm.wait()
    exe.interrupt()
    duration = time.time() - start_time
    assert duration < 2  # as long as its not too slow, we are fine.
    assert not pm._run_thread.is_alive()


def test_parallel_debug_info():
    w1 = WaitState('w1', 0.3)
    w2 = WaitState('w2', 0.3)
    pm = ParallelState("pm", [w1, w2])
    pm.start(None)
    pm.wait(0.1)
    info = pm.get_debug_info()
    assert info['name'] == 'pm'
    assert len(info['children']) == 2
    assert info['children'][0]['name'] == 'w1'
    assert info['children'][0]['status'] == StateStatus.RUNNING
    assert info['children'][1]['name'] == 'w2'
    assert info['children'][1]['status'] == StateStatus.RUNNING
    pm.interrupt()