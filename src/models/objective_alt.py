from collections import deque
from dataclasses import dataclass

from .objective import Objective
from .package import Package
from .problem import Problem
from .solution import State
from .truck import Truck


@dataclass(frozen=True)
class _PlacedItem:
    package: Package
    x: int
    y: int
    z: int
    dx: int
    dy: int
    dz: int
    volume: int
    base_value: float


class ObjectiveAlt(Objective):
    """Objective function alternatif: Sama seperti main objective function, 
    tetapi ditambah dengan melibatkan ETA paket, di mana ETA yang lebih kecil memberikan
    kontribusi nilai yang lebih besar, dikurangi penalty seluruh constraint.
    Implikasinya, paket yang dijanjikan datang lebih cepat (ETA lebih kecil) memiliki
    nilai yang lebih besar
    """

    def _package_value(self, package: Package) -> float:
        return float(package.value) / max(1, package.eta)

    def value(self, problem: Problem, state: State) -> float:
        packages_by_id = {pkg.id: pkg for pkg in problem.packages}
        trucks_by_id = {truck.id: truck for truck in problem.trucks}

        items_by_truck: dict[str, list[_PlacedItem]] = {
            truck.id: [] for truck in problem.trucks
        }

        total_value = 0.0
        total_penalty = 0.0

        for ps in state.package_states:
            if ps.placement is None:
                continue

            pkg = packages_by_id.get(ps.package_id)
            if pkg is None:
                continue

            vi = self._package_value(pkg)
            total_value += vi

            truck_id = ps.placement.truck_id
            if truck_id not in trucks_by_id:
                total_penalty += vi * 2.0
                continue

            x, y, z = ps.placement.position
            dx, dy, dz = pkg.oriented_dimensions(ps.orientation)
            volume = max(1, dx * dy * dz)

            items_by_truck[truck_id].append(
                _PlacedItem(
                    package=pkg,
                    x=x,
                    y=y,
                    z=z,
                    dx=dx,
                    dy=dy,
                    dz=dz,
                    volume=volume,
                    base_value=vi,
                )
            )

        for truck in problem.trucks:
            items = items_by_truck[truck.id]
            if not items:
                continue
            total_penalty += self._evaluate_truck_penalty(truck, items)

        return total_value - total_penalty

    def _evaluate_truck_penalty(
        self, truck: Truck, items: list[_PlacedItem]
    ) -> float:
        penalty = 0.0
        tw = truck.dimensions["w"]
        tl = truck.dimensions["l"]
        th = truck.dimensions["h"]
        n = len(items)

        # 1. Melebihi kapasitas berat truk
        total_weight = sum(item.package.weight for item in items)
        if total_weight > truck.max_capacity:
            truck_value = sum(item.base_value for item in items)
            if truck.max_capacity > 0:
                excess_ratio = (total_weight - truck.max_capacity) / truck.max_capacity
            else:
                excess_ratio = 1.0
            penalty += truck_value * (1.0 + excess_ratio)

        # 2. Menembus batas container truk
        for item in items:
            in_x = max(0, min(item.x + item.dx, tw) - max(item.x, 0))
            in_y = max(0, min(item.y + item.dy, tl) - max(item.y, 0))
            in_z = max(0, min(item.z + item.dz, th) - max(item.z, 0))
            vol_in = in_x * in_y * in_z
            vol_out = item.volume - vol_in

            if vol_out > 0:
                ratio_out = vol_out / item.volume
                penalty += item.base_value * (1.0 + ratio_out)

        # 3. Overlap antar paket di dalam truk yang sama
        for i in range(n):
            a = items[i]
            for j in range(i + 1, n):
                b = items[j]
                ov_x = max(0, min(a.x + a.dx, b.x + b.dx) - max(a.x, b.x))
                ov_y = max(0, min(a.y + a.dy, b.y + b.dy) - max(a.y, b.y))
                ov_z = max(0, min(a.z + a.dz, b.z + b.dz) - max(a.z, b.z))
                vol_ov = ov_x * ov_y * ov_z

                if vol_ov > 0:
                    ratio_a = vol_ov / a.volume
                    ratio_b = vol_ov / b.volume
                    penalty += a.base_value * (1.0 + ratio_a) + b.base_value * (
                        1.0 + ratio_b
                    )

        supports: list[list[tuple[int, int]]] = [[] for _ in range(n)]
        for lower_idx in range(n):
            lower = items[lower_idx]
            top_z = lower.z + lower.dz
            for upper_idx in range(n):
                if lower_idx == upper_idx:
                    continue
                upper = items[upper_idx]
                if upper.z != top_z:
                    continue
                ov_x = min(lower.x + lower.dx, upper.x + upper.dx) - max(
                    lower.x, upper.x
                )
                ov_y = min(lower.y + lower.dy, upper.y + upper.dy) - max(
                    lower.y, upper.y
                )
                if ov_x > 0 and ov_y > 0:
                    supports[lower_idx].append((upper_idx, ov_x * ov_y))

        # 4. Melayang (cascading paket di atasnya)
        grounded = [False] * n
        queue: deque[int] = deque()

        for idx, item in enumerate(items):
            if item.z == 0:
                grounded[idx] = True
                queue.append(idx)

        while queue:
            curr_idx = queue.popleft()
            for upper_idx, _ in supports[curr_idx]:
                if not grounded[upper_idx]:
                    grounded[upper_idx] = True
                    queue.append(upper_idx)

        max_h = max(1, th)
        for idx, item in enumerate(items):
            if not grounded[idx]:
                height_ratio = max(1, item.z) / max_h
                penalty += item.base_value * (1.0 + height_ratio)

        # 5. Package fragile ditimpa package lain (cascading paket di atasnya)
        on_fragile_ratio: dict[int, float] = {}
        fragile_queue: deque[int] = deque()

        for idx, item in enumerate(items):
            if item.package.is_fragile:
                fragile_queue.append(idx)

        while fragile_queue:
            curr_idx = fragile_queue.popleft()
            for upper_idx, contact_area in supports[curr_idx]:
                upper_item = items[upper_idx]
                upper_base_area = max(1, upper_item.dx * upper_item.dy)
                ratio = max(0.1, min(1.0, contact_area / upper_base_area))
                if upper_idx not in on_fragile_ratio:
                    on_fragile_ratio[upper_idx] = ratio
                    fragile_queue.append(upper_idx)
                else:
                    on_fragile_ratio[upper_idx] = max(
                        on_fragile_ratio[upper_idx], ratio
                    )

        for upper_idx, ratio in on_fragile_ratio.items():
            penalty += items[upper_idx].base_value * (1.0 + ratio)

        return penalty