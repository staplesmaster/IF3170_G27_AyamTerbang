import viser
import secrets
from ..models.solution import State
from ..models.problem import Problem

class Renderer:
    server: viser.ViserServer
    problem: Problem
    truckOrigins: dict[str, tuple[float, float]]

    truckHandles = list[viser.BoxHandle]
    packageHandles = dict[str, viser.BoxHandle]
    packageColors: dict[str, tuple[int, int, int]]

    def __init__(self, server: viser.ViserServer):
        self.server = server
        self.truckHandles = []
        self.packageHandles = {}
        self.packageColors = {}
        self.truckOrigins = {}
        self.problem = None

    def _cleanup(self):
        for h in self.truckHandles:
            h.remove()
        self.truckHandles.clear()
        for h in self.packageHandles.values():
            h.remove()
        self.packageHandles.clear()
        self.packageColors.clear()
        self.truckOrigins.clear()

    def _package_color(self, package):
        color = self.packageColors.get(package.id)
        if color is None:
            shade = secrets.randbelow(128) + 128
            accent = secrets.randbelow(64)
            color = (shade, accent, accent) if package.is_fragile else (accent, accent, shade)
            self.packageColors[package.id] = color
        return color

    def _render_trucks(self):
        gap = 2.0
        totalWidth = sum(t.dimensions["w"] for t in self.problem.trucks)
        totalWidth += gap * max(len(self.problem.trucks) - 1, 0)
        truckX = -totalWidth / 2

        for t in self.problem.trucks:
            width = t.dimensions["w"]
            truckLength = t.dimensions["l"]
            truckHeight = t.dimensions["h"]
            centerX = truckX + width / 2
            self.truckOrigins[t.id] = (truckX, 0.0)
            centerY = truckLength / 2
            self.truckHandles.append(self.server.scene.add_box(
                name=f"{t.id}",
                position=(centerX, centerY, truckHeight / 2),
                dimensions=(width, truckLength, truckHeight),
                color=(0, 0, 0),
                opacity=0.1,
            ))
            truckX += width + gap

    def _render_packages(self, state: State):
        package_states = {package_state.package_id: package_state for package_state in state.package_states}

        gap = 4
        unpacked = [p for p in self.problem.packages
                    if package_states.get(p.id) is None or package_states[p.id].placement is None]
        total_width = sum(p.oriented_dimensions(package_states[p.id].orientation)[0] for p in unpacked)
        total_width += gap * max(len(unpacked) - 1, 0)
        cursor_x = -total_width / 2
        for package in unpacked:
            dims = package.oriented_dimensions(package_states[package.id].orientation)
            center = (cursor_x + dims[0] / 2, -gap - dims[1] / 2, dims[2] / 2)
            self.packageHandles[package.id] = self.server.scene.add_box(
                name=f"packages/{package.id}", position=center, dimensions=dims,
                color=self._package_color(package),
            )
            cursor_x += dims[0] + gap

        for package in self.problem.packages:
            package_state = package_states.get(package.id)
            placement = package_state.placement if package_state is not None else None
            if placement is None:
                continue
            truck = next((t for t in self.problem.trucks if t.id == placement.truck_id), None)
            if truck is None or truck.id not in self.truckOrigins:
                continue
            dims = package.oriented_dimensions(package_state.orientation)
            origin_x, origin_y = self.truckOrigins[truck.id]
            x, y, z = placement.position
            handle = self.server.scene.add_box(
                name=f"packages/{package.id}",
                position=(origin_x + x + dims[0] / 2, origin_y + y + dims[1] / 2, z + dims[2] / 2),
                dimensions=dims,
                color=self._package_color(package),
            )
            self.packageHandles[package.id] = handle

    def _move_packages(self, state: State):
        package_states = {package_state.package_id: package_state for package_state in state.package_states}

        gap = 4
        unpacked = [p for p in self.problem.packages
                    if package_states.get(p.id) is None or package_states[p.id].placement is None]
        total_width = sum(p.oriented_dimensions(package_states[p.id].orientation)[0] for p in unpacked)
        total_width += gap * max(len(unpacked) - 1, 0)
        cursor_x = -total_width / 2

        for package in self.problem.packages:
            package_state = package_states.get(package.id)
            if package_state is None:
                continue
            dims = package.oriented_dimensions(package_state.orientation)
            placement = package_state.placement
            handle = self.packageHandles.get(package.id)
            if handle is None:
                continue
            handle.dimensions = dims
            if placement is None:
                handle.position = (cursor_x + dims[0] / 2, -gap - dims[1] / 2, dims[2] / 2)
                cursor_x += dims[0] + gap
            elif placement.truck_id in self.truckOrigins:
                x, y, z = placement.position
                origin_x, origin_y = self.truckOrigins[placement.truck_id]
                handle.position = (origin_x + x + dims[0] / 2,
                                   origin_y + y + dims[1] / 2,
                                   z + dims[2] / 2)

    def render(self, problem: Problem, state: State):
        if self.problem != problem:
            self._cleanup()
            self.problem = problem
            self._render_trucks()
            self._render_packages(state)
        else:
            self._move_packages(state)
