
from behavior_machine.library.parallel_state import ParallelState
from behavior_machine.library.sequential_state import SequentialState
from behavior_machine.core import State, Machine, Board, StateStatus
from behavior_machine.library import IdleState
from behavior_machine.visualization import visualize_behavior_machine



def make_machine(name):
    s1 = IdleState("s1")
    s2 = IdleState("s2")

    s1.add_transition_on_success(s2)

    return Machine(name, s1)

m1 = make_machine("m1")
m2 = make_machine("m2")
m1.add_transition_on_success(m2)
xe = IdleState('xe')
m2.add_transition_on_failed(xe)

ss = SequentialState("ss", children=[
    IdleState("i1"),
    IdleState("i2"),
    IdleState("i3"),
    IdleState("i4"),
])
pp = ParallelState("pp", children=[
    IdleState("i1"),
    IdleState("i2"),
])

xe.add_transition_on_complete(ss)
xe.add_transition_on_complete(pp)



exe = Machine('exe', m1, rate=5)

visualize_behavior_machine(exe, "mac.png")