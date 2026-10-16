from ..models.problem import Problem
from ..models.package import Package
from ..models.truck import Truck
from .input import PackageConfig, TruckConfig, ProblemConfig
from pydantic import ValidationError

class Parser:
    def _parse_trucks(self, configs: list[TruckConfig]) -> tuple[Truck, ...]:
        return tuple(
            Truck(config.id, config.dimensions, config.maxCapacity)
            for config in configs
        )
    
    def _parse_packages(self, configs: list[PackageConfig]) -> tuple[Package, ...]:
        packages = []
        for config in configs:
            axis_dimensions = {
                axis: dimension for dimension, axis in config.orientation.items()
            }
            orientation = tuple(axis_dimensions[axis] for axis in ("x", "y", "z"))
            packages.append(
                Package(
                    id=config.id,
                    dimensions=config.dimensions,
                    initial_orientation=orientation,
                    value=config.value,
                    weight=config.weight,
                    is_fragile=config.isFragile,
                    eta=config.eta,
                )
            )
        return tuple(packages)

    def parse(self, source: object) -> Problem:
        try:
            payload = getattr(source, "content", source)
            config = ProblemConfig.model_validate_json(payload)
            return Problem(
                packages=self._parse_packages(config.packages),
                trucks=self._parse_trucks(config.trucks),
            )
        except ValidationError:
            raise RuntimeError