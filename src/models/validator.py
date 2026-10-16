from abc import ABC, abstractmethod

from .problem import Problem
from .solution import State


class PackingValidator(ABC):
    @abstractmethod
    def validate(self, problem: Problem, state: State) -> bool:
        """Check truck boundaries, overlap, capacity, and package support."""
        raise NotImplementedError