from pydantic import BaseModel

class TruckConfig(BaseModel):
    id: str
    dimensions: dict[str, int]
    maxCapacity: int

class PackageConfig(BaseModel):
    id: str
    dimensions: dict[str, int]
    orientation: dict[str, str]
    value: int
    weight: int
    isFragile: bool
    eta: int

class ProblemConfig(BaseModel):
    trucks: list[TruckConfig]
    packages: list[PackageConfig]