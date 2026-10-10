from abc import ABC, abstractmethod

from ..models.problem import Problem
from ..models.solution import Solution


class Algorithm(ABC):
    @abstractmethod
    def solve(self, problem: Problem) -> Solution:
        raise NotImplementedError