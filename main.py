"""
Finite‑state machine regex engine
Nikita Lenyk
"""

from abc import ABC, ABCMeta, abstractmethod


class StateMeta(ABCMeta):
    """
    Metaclass for State class. It adds the __mul__ method to the State class.
    """

    def __new__(mcs: type, name: str, bases: tuple, namespace: dict):
        """
        This method is called when a new class is created.
        Adds the __mul__method into namespace of the class.

        Args:
            mcs (type): metaclass
            name (str): name of the class
            bases (tuple): tuple of base classes
            namespace (dict): namespace of the class
        """

        def __mul__(self, _other: "State") -> "State":
            """
            This method is called when the * operator is used on a State object.

            Args:
                _other (State): unused argument

            Returns:
                State: a new StarState object
            """
            return StarState(self)

        namespace["__mul__"] = __mul__
        return super().__new__(mcs, name, bases, namespace)


class State(ABC, metaclass=StateMeta):
    """
    Base class for all states.
    """

    def __init__(self) -> None:
        self.is_final: bool = False
        self.next_states: list["State"] = []

    @abstractmethod
    def check_self(self, char: str) -> bool:
        """
        Check if the character is accepted by the state.

        Args:
            char (str): the character to check

        Returns:
            bool: True if the character is accepted by the state, False otherwise
        """
        pass

    def check_next(self, next_char: str) -> "State":
        """
        Check the next character and return the next state.

        Args:
            next_char (str): the next character to check

        Raises:
            NotImplementedError: if the next character is not accepted by any state

        Returns:
            State: a state that accepts the next character
        """
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        raise NotImplementedError("rejected string")

    def __repr__(self) -> str:
        """
        Returns a string representation of the state.

        Returns:
            str: string representation of the state
        """
        return f"{self.__class__.__name__}(final={self.is_final})"


class StartState(State):
    """
    Start state of the FSM. It is the first state in the FSM.
    """

    def check_self(self, _: str) -> bool:
        """
        Override the check_self method to always return False.

        Args:
            _ (str): the character to check (not used)

        Returns:
            bool: always False
        """
        return False


class TerminationState(State):
    """
    Termination state of the FSM. It is the last state in the FSM.
    """

    def __init__(self) -> None:
        super().__init__()
        self.is_final = True

    def check_self(self, _: str) -> bool:
        """
        Override the check_self method to always return False.

        Args:
            _ (str): the character to check (not used)

        Returns:
            bool: always False
        """
        return False


class DotState(State):
    """
    Dot state of the FSM. It accepts any character.
    """

    def check_self(self, _: str) -> bool:
        """
        Override the check_self method to always return True.

        Args:
            _ (str): the character to check (not used)

        Returns:
            bool: always True
        """
        return True


class AsciiState(State):
    """
    Ascii state of the FSM. It accepts a single character.
    """

    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.symbol = symbol

    def check_self(self, char: str) -> bool:
        """
        Override the check_self method to check if the character is equal to the symbol.

        Args:
            char (str): the character to check

        Returns:
            bool: True if the character is equal to the symbol, False otherwise
        """
        return char == self.symbol

    def __repr__(self) -> str:
        """
        Returns a string representation of the state.

        Returns:
            str: string representation of the state
        """
        return f"AsciiState('{self.symbol}', final={self.is_final})"


class ClassState(State):
    """
    CharClassState is a state that accepts a set of characters.
    """

    def __init__(self, chars: set[str], ignore: bool = False) -> None:
        super().__init__()
        self.chars = chars
        self.ignore = ignore

    def check_self(self, char: str) -> bool:
        """
        Check if the character is in the set of characters.

        Args:
            char (str): the character to check

        Returns:
            bool: True if the character is in the set, False otherwise
        """
        return char not in self.chars if self.ignore else char in self.chars

    def __repr__(self) -> str:
        """
        Returns a string representation of the state.

        Returns:
            str: string representation of the state
        """
        prefix = "^" if self.ignore else ""
        chars = "".join(sorted(self.chars))
        return f"CharClassState('{prefix}[{chars}]', final={self.is_final})"


class StarState(State):
    """
    StarState is a state that accepts zero or more occurrences of the base state.
    """

    def __init__(self, base: State) -> None:
        super().__init__()
        self.base = base
        self.is_final = True

    def check_self(self, char: str) -> bool:
        """
        Check if the character is accepted by the base state.

        Args:
            char (str): the character to check

        Returns:
            bool: True if the character is accepted by the base state, False otherwise
        """
        return self.base.check_self(char)

    def check_next(self, next_char: str) -> "State":
        """
        Check the next character and return the next state.

        Args:
            next_char (str): the next character to check

        Returns:
            State: a state that accepts the next character
        """
        if self.check_self(next_char):
            return self
        return super().check_next(next_char)


class RegexFSM:
    """
    FSM builder for regex patterns.
    """

    def __init__(self, regex_pattern: str) -> None:
        self.regex_pattern = regex_pattern
        self.start_state = StartState()

        prev_state: State = self.start_state
        prev_prev_state: State | None = None

        i = 0
        while i < len(regex_pattern):
            char = regex_pattern[i]

            match char:
                case "*" | "+":
                    star_state = prev_state * None

                    if char == "*" and RegexFSM.star_followed_by_charclass_plus(
                        regex_pattern, i
                    ):
                        star_state.is_final = False

                    if char == "*":
                        edge_from = prev_prev_state or self.start_state
                        edge_from.next_states.append(star_state)

                    prev_state.next_states.append(star_state)
                    prev_prev_state, prev_state = prev_state, star_state
                    i += 1

                case "[":
                    j = regex_pattern.find("]", i + 1)
                    if j == -1:
                        raise ValueError("Unclosed character class")

                    content = regex_pattern[i + 1 : j]
                    ignore = content.startswith("^")
                    if ignore:
                        content = content[1:]

                    chars: set[str] = set()
                    k = 0
                    while k < len(content):
                        if k + 2 < len(content) and content[k + 1] == "-":
                            for code in range(ord(content[k]), ord(content[k + 2]) + 1):
                                chars.add(chr(code))
                            k += 3
                        else:
                            chars.add(content[k])
                            k += 1

                    state = ClassState(chars, ignore)
                    prev_state.next_states.append(state)
                    prev_prev_state, prev_state = prev_state, state
                    i = j + 1

                case ".":
                    state = DotState()
                    prev_state.next_states.append(state)
                    prev_prev_state, prev_state = prev_state, state
                    i += 1
                case _:
                    state = AsciiState(char)
                    prev_state.next_states.append(state)
                    prev_prev_state, prev_state = prev_state, state
                    i += 1

        terminator = TerminationState()
        prev_state.next_states.append(terminator)

    @staticmethod
    def star_followed_by_charclass_plus(expr: str, star_idx: int) -> bool:
        """
        Check if the star is followed by a character class and a plus sign.

        Args:
            expr (str): expression to check
            star_idx (int): index of the star

        Returns:
            bool: True if the star is followed by a character class and a plus sign, False otherwise
        """

        if star_idx + 1 >= len(expr) or expr[star_idx + 1] != "[":
            return False

        j = expr.find("]", star_idx + 2)
        return j != -1 and j + 1 < len(expr) and expr[j + 1] == "+"

    def check_string(self, text: str) -> bool:
        """
        Check if the string is accepted by the FSM.

        Args:
            text (str): string to check

        Returns:
            bool: True if the string is accepted by the FSM, False otherwise
        """
        current: set[State] = {self.start_state}
        for char in text:
            current |= {
                next_state
                for state in current
                for next_state in state.next_states
                if isinstance(next_state, StarState) and next_state.is_final
            }
            next_states: set[State] = set()
            for st in current:
                try:
                    next_states.add(st.check_next(char))
                except NotImplementedError:
                    pass
            if not next_states:
                return False
            current = next_states

        current |= {
            next_state
            for state in current
            for next_state in state.next_states
            if next_state.is_final
        }
        return any(st.is_final for st in current)


if __name__ == "__main__":
    fsm = RegexFSM("a*b")
    assert fsm.check_string("b") is True
    assert fsm.check_string("aaaab") is True
    assert fsm.check_string("ab") is True
    assert fsm.check_string("c") is False

    fsm = RegexFSM("a+b")
    assert fsm.check_string("b") is False
    assert fsm.check_string("ab") is True
    assert fsm.check_string("aab") is True

    fsm = RegexFSM("ab+c")
    assert fsm.check_string("abc") is True
    assert fsm.check_string("abbbbbc") is True
    assert fsm.check_string("ac") is False

    fsm = RegexFSM("ab+c*d")
    assert fsm.check_string("abc") is True

    fsm = RegexFSM("a*4*.+hi")
    assert fsm.check_string("aaaaaaaa4uhi") is True
    assert fsm.check_string("4uhi") is True
    assert fsm.check_string("meow") is False

    fsm = RegexFSM("[a-c]+d")
    assert fsm.check_string("acccd") is True
    assert fsm.check_string("bbd") is True
    assert fsm.check_string("ed") is False

    fsm = RegexFSM("[^x-z]*1")
    assert fsm.check_string("abc1") is True
    assert fsm.check_string("xy1") is False

    pattern0 = "a*4.+hi"
    fsm0 = RegexFSM(pattern0)
    assert fsm0.check_string("aaaaaa4uhi")
    assert fsm0.check_string("4uhi")
    assert fsm0.check_string("a4.hi")
    assert fsm0.check_string("444hi")
    assert not fsm0.check_string("meow")

    pattern1 = "[a-c]+[d-f]+[g-i]*"
    fsm1 = RegexFSM(pattern1)
    assert fsm1.check_string("abcddggg")
    assert fsm1.check_string("aaadef")
    assert fsm1.check_string("bcdfi")
    assert fsm1.check_string("ccdd")
    assert fsm1.check_string("abcd")
    assert not fsm1.check_string("xyz")

    pattern2 = "[a-zsh]*[^a-z]+"
    fsm2 = RegexFSM(pattern2)
    assert fsm2.check_string("shs123")
    assert fsm2.check_string("abcm@#")
    assert fsm2.check_string("shtT")
    assert not fsm2.check_string("shshabc")
    assert not fsm2.check_string("")

    pattern3 = "[^a-z]+[A-Z]*"
    fsm3 = RegexFSM(pattern3)
    assert fsm3.check_string("123ABC")
    assert fsm3.check_string("@@Z")
    assert fsm3.check_string("TTT")
    assert fsm3.check_string("##")
    assert not fsm3.check_string("abc")
    assert not fsm3.check_string("aZ")
