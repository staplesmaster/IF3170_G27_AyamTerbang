from abc import ABC, abstractmethod

from .problem import Problem
from .solution import Solution

class Objective(ABC):

    @abstractmethod
    def value(self, problem: Problem, solution: Solution) -> float:
        """Return the objective value of a candidate solution."""
        pass