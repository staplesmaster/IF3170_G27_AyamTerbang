from abc import ABC, abstractmethod

from ..models.problem import Problem
from ..models.solution import State


class Algorithm(ABC):
    @abstractmethod
    def solve(self, problem: Problem) -> State:
        raise NotImplementedError