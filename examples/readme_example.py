from behavior_machine.core import State, Machine
from behavior_machine.library import PrintState, SequentialState, IdleState
from behavior_machine.visualization import visualize_behavior_machine


ps1 = PrintState("ps1", "Hello World 1")
ps2 = PrintState("ps2", "Hello World 2")
is1 = IdleState("is1")
ps3 = PrintState("ps3", "Hello World 3")

ss = SequentialState("ss", children=[ps1, ps2])
ss.add_transition_on_success(ps3)

m1 = Machine("m1", ss, rate=10)
m1.add_transition(lambda state, board: state._curr_state._name == "ps3", is1)
m2 = Machine("m2", m1, end_state_ids=['is1'], rate=10)
m2.run()


visualize_behavior_machine(m2, "readme.png")