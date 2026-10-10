from dataclasses import dataclass
from itertools import permutations


@dataclass(frozen=True)
class Package:
    id: str
    dimensions: dict[str, int]
    initial_orientation: tuple[str, str, str]
    value: int
    weight: int
    is_fragile: bool
    eta: int

    def oriented_dimensions(
        self, orientation: tuple[str, str, str] | None = None
    ) -> tuple[int, int, int]:
        axes = orientation or self.initial_orientation
        return tuple(self.dimensions[dimension] for dimension in axes)

    def possible_orientations(self) -> tuple[tuple[str, str, str], ...]:
        rotations = tuple(permutations(self.dimensions))
        return (self.initial_orientation,) + tuple(
            rotation for rotation in rotations if rotation != self.initial_orientation
        )

    @property
    def isFragile(self) -> bool:
        return self.is_fragile