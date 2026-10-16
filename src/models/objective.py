from abc import ABC, abstractmethod

from .problem import Problem
from .solution import State

class Objective(ABC):

    @abstractmethod
    def value(self, problem: Problem, state: State) -> float:
        """Return the objective value of a candidate solution."""
        pass