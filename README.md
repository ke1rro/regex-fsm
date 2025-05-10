# Finite State Machine for Regex

The project implements a finite state machine (FSM) for recognizing regular expressions. It is designed to be simple and efficient, allowing users to create FSMs from regex patterns and test strings against them.

## Features

- Create FSMs from regex patterns

- Test strings against FSMs

- Support for basic regex constructs (characters, unions, concatenation, and Kleene star) `+, *, .`

- Support for character classes `[a-z]`

- Support for negation  `[^a-z]`

## Key Components

- `RegexFSM`: The main class representing the finite state machine. It parses regex patterns and builds the corresponding state machine.

- `State`: An abstract base class (ABC) that defines the interface for all state types. It uses the `StateMeta` metaclass to add operator overloading capability.

- `StateMeta`: A metaclass that adds the `__mul__` method to all State subclasses, enabling the Kleene star operation through the `*` operator.

- `StartState`: The initial state in the FSM.

- `TerminationState`: The final accepting state of the FSM.

- `AsciiState`: Represents a state that accepts a single specific character.

- `DotState`: Represents a state that accepts any character

- `ClassState`: Handles character classes like `[a-z]` and ignore classes `[^a-z]`.

- `StarState`: Implements the Kleene star operation, allowing zero or more repetitions of a pattern.

## Usage

```python
fsm = RegexFSM("a*b")
assert fsm.check_string("b") is True
assert fsm.check_string("aaaab") is True
assert fsm.check_string("c") is False
```
