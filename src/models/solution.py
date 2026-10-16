from dataclasses import dataclass


@dataclass(frozen=True)
class Placement:
    package_id: str
    truck_id: str
    position: tuple[int, int, int]
    orientation: tuple[str, str, str]


@dataclass(frozen=True)
class State:
    placements: tuple[Placement, ...] = ()

    @property
    def placed_package_ids(self) -> frozenset[str]:
        return frozenset(placement.package_id for placement in self.placements)