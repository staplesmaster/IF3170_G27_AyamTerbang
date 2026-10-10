from dataclasses import dataclass


@dataclass(frozen=True)
class Truck:
    id: str
    dimensions: dict[str, int]
    max_capacity: int

    @property
    def maxCapacity(self) -> int:
        return self.max_capacity

