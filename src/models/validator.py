from abc import ABC, abstractmethod

from .problem import Problem
from .solution import Solution


class PackingValidator(ABC):
    @abstractmethod
    def validate(self, problem: Problem, solution: Solution) -> bool:
        """Check truck boundaries, overlap, capacity, and package support."""
        raise NotImplementedError