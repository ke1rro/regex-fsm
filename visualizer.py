import os

import graphviz

from main import (
    AsciiState,
    ClassState,
    DotState,
    RegexFSM,
    StarState,
    StartState,
    State,
    TerminationState,
)


class FSMVisualizer:
    """
    Visualizes a Finite State Machine using Graphviz.

    This class generates a visual representation of a RegexFSM using Graphviz.
    It shows states as nodes and transitions as edges, with appropriate labels.
    """

    def __init__(self, fsm: RegexFSM = None, pattern: str = None):
        """
        Initialize the visualizer with a RegexFSM or a regex pattern.

        Args:
            fsm (RegexFSM, optional): The FSM to visualize
            pattern (str, optional): A regex pattern to create an FSM
        """
        if fsm is None and pattern is None:
            raise ValueError("Either fsm or pattern must be provided.")

        if fsm is None:
            self.fsm = RegexFSM(pattern)
            self.pattern = pattern
        else:
            self.fsm = fsm
            self.pattern = fsm.regex_pattern

        self.dot = graphviz.Digraph(comment=f"Regex FSM for: {self.pattern}")

        self.dot.attr(rankdir="LR", size="8,5", fontname="Helvetica", dpi="300")

        self.dot.attr(
            "node",
            fontname="Helvetica",
            fontsize="12",
            margin="0.1,0.1",
            height="0.6",
            width="0.6",
        )
        self.dot.attr("edge", fontname="Helvetica", fontsize="10", arrowsize="0.7")

        self.visited_states = set()
        self.edges = set()

    def _get_state_id(self, state: State) -> str:
        """Get a unique ID for a state."""
        return f"state_{id(state)}"

    def _get_state_label(self, state: State) -> str:
        """Get a human-readable label for a state."""
        if isinstance(state, StartState):
            return "Start"
        elif isinstance(state, TerminationState):
            return "End"
        elif isinstance(state, AsciiState):
            return f"'{state.symbol}'"
        elif isinstance(state, DotState):
            return "."
        elif isinstance(state, ClassState):
            prefix = "^" if state.ignore else ""
            chars = "".join(sorted(state.chars))
            return f"[{prefix}{chars}]"
        elif isinstance(state, StarState):
            base_label = self._get_state_label(state.base)
            return f"{base_label}*"
        else:
            return state.__class__.__name__

    def _get_transition_label(self, state: State, next_state: State) -> str:
        """Get a label for a transition between two states."""
        if isinstance(next_state, AsciiState):
            return next_state.symbol
        elif isinstance(next_state, DotState):
            return "."
        elif isinstance(next_state, ClassState):
            prefix = "^" if next_state.ignore else ""
            chars = "".join(sorted(next_state.chars))
            if len(chars) > 10:
                # Truncate long character classes
                chars = chars[:5] + "..." + chars[-2:]
            return f"[{prefix}{chars}]"
        elif isinstance(next_state, TerminationState):
            return "ε"  # Epsilon for transition to end state
        elif isinstance(next_state, StarState):
            if isinstance(state, StarState) and state.base == next_state.base:
                # Self loop for star state
                if isinstance(state.base, AsciiState):
                    return state.base.symbol
                elif isinstance(state.base, DotState):
                    return "."
                elif isinstance(state.base, ClassState):
                    prefix = "^" if state.base.ignore else ""
                    chars = "".join(sorted(state.base.chars))
                    if len(chars) > 10:
                        chars = chars[:5] + "..." + chars[-2:]
                    return f"[{prefix}{chars}]"
            return "ε"
        else:
            return ""

    def _get_state_style(self, state: State) -> dict:
        """Get style attributes for a state."""
        style = {}

        if isinstance(state, StartState):
            style["shape"] = "circle"
        elif isinstance(state, TerminationState):
            style["shape"] = "doublecircle"
            style["penwidth"] = "2"
        elif state.is_final:
            style["shape"] = "doublecircle"
            style["penwidth"] = "2"
        elif isinstance(state, StarState):
            style["shape"] = "circle"
        elif isinstance(state, AsciiState):
            style["shape"] = "circle"
        elif isinstance(state, DotState):
            style["shape"] = "circle"
        elif isinstance(state, ClassState):
            style["shape"] = "box"
            style["style"] = "rounded"
        else:
            style["shape"] = "circle"

        return style

    def _build_graph(self, state: State, parent_id: str = None):
        """Recursively build the graph from a state."""
        state_id = self._get_state_id(state)
        if state_id not in self.visited_states:
            self.visited_states.add(state_id)
            label = self._get_state_label(state)
            style = self._get_state_style(state)
            self.dot.node(state_id, label, **style)
            for next_state in state.next_states:
                next_id = self._get_state_id(next_state)
                edge_key = (state_id, next_id)
                if edge_key not in self.edges:
                    self.edges.add(edge_key)
                    transition_label = self._get_transition_label(state, next_state)
                    self.dot.edge(state_id, next_id, label=transition_label)
                self._build_graph(next_state)
        if parent_id is not None:
            edge_key = (parent_id, state_id)
            if edge_key not in self.edges:
                self.edges.add(edge_key)
                transition_label = self._get_transition_label(None, state)
                self.dot.edge(parent_id, state_id, label=transition_label)
        if isinstance(state, StarState):
            edge_key = (state_id, state_id)
            if edge_key not in self.edges:
                self.edges.add(edge_key)
                loop_label = self._get_transition_label(state, state)
                self.dot.edge(state_id, state_id, label=loop_label)

    def visualize(
        self, output_path: str = None, view: bool = True, format: str = "png"
    ):
        """
        Visualize the FSM and save the result.

        Args:
            output_path (str, optional): Path to save the visualization
            view (bool, optional): Whether to open the result. Defaults to True
            format (str, optional): The output format. Defaults to 'png'

        Returns:
            str: The path to the saved visualization
        """
        if output_path is None:
            sanitized = self.pattern.replace("*", "star").replace("+", "plus")
            sanitized = sanitized.replace("[", "").replace("]", "").replace("^", "not")
            sanitized = "".join(
                c if c.isalnum() or c == "_" else "_" for c in sanitized
            )
            output_path = f"fsm_{sanitized[:30]}"
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.dot.format = format

        self._build_graph(self.fsm.start_state)
        return self.dot.render(output_path, view=view, cleanup=True)

    @classmethod
    def from_pattern(cls, pattern: str):
        """Create a visualizer from a regex pattern."""
        return cls(pattern=pattern)


if __name__ == "__main__":
    FSMVisualizer.from_pattern("a*b").visualize()
