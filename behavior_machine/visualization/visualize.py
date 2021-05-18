

from behavior_machine.library import sequential_state
from behavior_machine.core.machine import Machine
from ..core import State
from ..library import SequentialState, ParallelState, AtLeastOneState, SelectorState
import pygraphviz as pgv
import typing



def _recursive_visualize_state(state: State, graph: pgv.AGraph, visited_list: typing.List[str], leaf_list: typing.Mapping[str, str]) -> str:


    # get name of state
    state_name = state._name
    parent_name = graph.name
    # remove cluster if it is part of it 
    if parent_name.startswith("cluster_"):
        parent_name = parent_name[8:]
    global_name = f"{parent_name}_{state_name}"
    valid_node_name = ""

    # [Base Case]  ignore if we already visited it.
    if state_name in visited_list:
        return

    # Check if its a nest class or machine
    sub_graph = None
    if not hasattr(state, "_children") and not isinstance(state, Machine):
        # add it to the graph
        graph.add_node(global_name)
        valid_node_name = global_name
    else:
        sub_graph = graph.add_subgraph(name=f"cluster_{global_name}", label=state_name)
        if isinstance(state, Machine):
            state: Machine
            sub_graph.graph_attr["pencolor"] = "red"
            valid_node_name = _recursive_visualize_state(state._root, sub_graph, [], {})
        else:
            if isinstance(state, SequentialState) or isinstance(state, SelectorState):
                sub_graph.graph_attr["pencolor"] = "green"
                if isinstance(state, SelectorState):
                    sub_graph.graph_attr["pencolor"] = "yellow"

                prev_valid_name = ""
                for children in state._children:
                    valid_node_name = _recursive_visualize_state(children, sub_graph, [], {})
                    if prev_valid_name is not "":
                        sub_graph.add_edge(prev_valid_name, valid_node_name)
                    prev_valid_name = valid_node_name
            else:
                sub_graph.graph_attr["pencolor"] = "blue"
                for children in state._children:
                    valid_node_name = _recursive_visualize_state(children, sub_graph, [], {})

    # registered as visited
    visited_list.append(state_name)
    leaf_list[state_name] = valid_node_name

    # Add transition for each state
    for transition in state._transitions:    
        # get a reference to the next state
        func_trans = transition[0]
        nxt_state = transition[1]
        nxt_state_name = nxt_state._name
        # ignore visited states except for self-loop
        if nxt_state_name not in visited_list:
            # visit that state
            nxt_valid_node_name = _recursive_visualize_state(nxt_state, graph, visited_list, leaf_list)
        else:
            nxt_valid_node_name = leaf_list[state_name]

        # construct the name if its a cluster
        nxt_cluster_name = f"cluster_{parent_name}_{nxt_state_name}"

        # HACK: graphviz require nodes to be linked up and cannot use cluster. Their way is to just hide it
        if graph.get_subgraph(nxt_cluster_name) is None:
            if sub_graph is None:
                graph.add_edge(valid_node_name, nxt_valid_node_name)
            else:
                graph.add_edge(valid_node_name, nxt_valid_node_name, ltail=sub_graph.name)
        else:
            nxt_graph = graph.get_subgraph(nxt_cluster_name)
            if sub_graph is None:
                graph.add_edge(valid_node_name, nxt_valid_node_name, lhead=nxt_graph.name)
            else:
                graph.add_edge(valid_node_name, nxt_valid_node_name, ltail=sub_graph.name, lhead=nxt_graph.name)
    
    return valid_node_name

def visualize_behavior_machine(root_state: State, output_path:str):

    # create graph
    graph = pgv.AGraph(strict=False, directed=True, name="root", compound=True)

    # use the recursive function
    _recursive_visualize_state(root_state, graph, [], {})

    # create a fake legend
    graph.add_node("legend_m", color="red", label="Machine")
    graph.add_node("legend_s", color="green", label="Sequential")
    graph.add_node("legend_p", color="blue", label="Parallel")

    # create the graph layout and draw
    graph.layout(prog="dot")
    print(graph)
    graph.draw(output_path)
