from dataclasses import dataclass

from .package import Package
from .truck import Truck


@dataclass(frozen=True)
class Problem:
    packages: tuple[Package, ...]
    trucks: tuple[Truck, ...]