from typing import Callable, Dict, Set


class State:

    _name: str

    def __init__(self, name: str):
        self._name = name

    def __hash__(self) -> int:
        return hash(self._name)

    def __eq__(self, other: 'State') -> bool:
        return self._name == other.name

    def __str__(self):
        return self._name

    @property
    def name(self) -> str:
        return self._name


class StateMachine:

    class InvalidTransitionError(Exception):

        def __init__(self, message: str):
            self.message = message
            super().__init__(self.message)

    _initial_state: State
    _current_state: State
    _states: Set[State]
    _accepting_states: Set[State]
    _transitions: Dict[State, Set[State]]
    _callbacks: Dict[State, Dict[State, Callable]]

    def __init__(self):
        self._initial_state = None
        self._current_state = None
        self._states = set()
        self._accepting_states = set()
        self._transitions = {}
        self._callbacks = {}

    def add_state(
        self, name: str, is_initial: bool = False, is_accpeting: bool = False
    ) -> State:
        state = State(name)
        if state in self._states:
            raise ValueError("There already exists a state with this name")
        self._states.add(state)
        self._callbacks[state] = {}
        if is_initial:
            if self._initial_state:
                raise ValueError("There already exists an initial state")
            self._initial_state = state
            self._current_state = state
        if is_accpeting:
            self._accepting_states.add(state)
        return state

    def add_transition(self, source: State, target: State, callback: Callable):
        if source not in self._states:
            raise ValueError(f"Unknown state: {source}")
        if target not in self._states:
            raise ValueError(f"Unknown state: {target}")
        if source not in self._transitions.keys():
            self._transitions[source] = set()
        self._transitions[source].add(target)
        self._callbacks[source][target] = callback

    def transition(self, state: State, *args, **kwargs):
        if state not in self._transitions[self._current_state]:
            raise self.InvalidTransitionError(
                f"Invalid Transition: {self} -> {state}"
            )
        self._callbacks[self._current_state][state](*args, **kwargs)
        self._current_state = state

    def reset(self):
        self._current_state = self._initial_state

    @property
    def is_initial(self) -> bool:
        return self._current_state == self._initial_state

    @property
    def is_accpeting(self) -> bool:
        return self._current_state in self._accepting_states

    @property
    def state(self):
        return self._current_state
