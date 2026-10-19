from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from ..models.problem import Problem
from ..models.solution import State
from ..models.solution import Result


@dataclass(frozen=True)
class AlgorithmOption:
    key: str
    label: str
    kind: Literal["number", "slider", "checkbox"]
    default: int | float | bool
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None


class Algorithm(ABC):
    def get_options(self) -> list[AlgorithmOption]:
        """Return the controls this algorithm needs; override in subclasses."""
        return []

    @abstractmethod
    def solve(self, problem: Problem, state: State, options: dict[str]) -> Result:
        raise NotImplementedError

    @abstractmethod
    def getName(self) -> str:
        raise NotImplementedError
