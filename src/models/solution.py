from dataclasses import dataclass


@dataclass(frozen=True)
class Placement:
    truck_id: str
    position: tuple[int, int, int]


@dataclass(frozen=True)
class PackageState:
    package_id: str
    orientation: tuple[str, str, str]
    placement: Placement | None = None


@dataclass(frozen=True)
class State:
    package_states: tuple[PackageState, ...] = ()

    @classmethod
    def from_problem(cls, problem) -> "State":
        return cls(
            tuple(
                PackageState(
                    package_id=package.id,
                    orientation=package.initial_orientation,
                )
                for package in problem.packages
            )
        )

    @property
    def placed_package_ids(self) -> frozenset[str]:
        return frozenset(
            package_state.package_id
            for package_state in self.package_states
            if package_state.placement is not None
        )