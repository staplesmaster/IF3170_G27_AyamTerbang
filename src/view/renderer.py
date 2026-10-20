import colorsys
import viser
from ..models.solution import Result, State
from ..models.problem import Problem


class Renderer:
    server: viser.ViserServer
    problem: Problem | None
    truckOrigins: dict[str, tuple[float, float]]

    truckHandles: list[viser.BoxHandle]
    packageHandles: dict[str, viser.BoxHandle]
    packageColors: dict[str, tuple[int, int, int]]

    # Warna kontainer truk dibuat gelap-kontras (slate steel) agar paket berwarna cerah menonjol
    TRUCK_BASE_COLOR: tuple[int, int, int] = (45, 55, 72)
    TRUCK_WALL_COLOR: tuple[int, int, int] = (74, 85, 104)

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

    def _generate_package_colors(self) -> None:
        """Bangkitkan warna yang saling kontras untuk setiap package menggunakan
        distribusi golden-ratio pada ruang warna HSV.
        """
        self.packageColors.clear()
        if self.problem is None:
            return

        golden_ratio_conjugate = 0.618033988749895
        for idx, package in enumerate(self.problem.packages):
            hue = (idx * golden_ratio_conjugate) % 1.0
            # Variasikan sedikit saturasi dan value agar makin mudah dibedakan
            saturation = 0.78 if idx % 2 == 0 else 0.90
            value = 0.95 if idx % 3 != 0 else 0.82
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
            self.packageColors[package.id] = (
                int(round(r * 255)),
                int(round(g * 255)),
                int(round(b * 255)),
            )

    def _render_trucks(self):
        gap = 3.0
        line_t = 0.04  # Ketebalan garis grid
        grid_color = (90, 105, 125)
        frame_color = (40, 50, 65)

        totalWidth = sum(t.dimensions["w"] for t in self.problem.trucks)
        totalWidth += gap * max(len(self.problem.trucks) - 1, 0)
        truckX = -totalWidth / 2

        for t in self.problem.trucks:
            w = t.dimensions["w"]
            l = t.dimensions["l"]
            h = t.dimensions["h"]
            self.truckOrigins[t.id] = (truckX, 0.0)

            # 1. Grid Alas (Bidang XY pada z = 0)
            for ix in range(w + 1):
                is_edge = ix in (0, w)
                self.truckHandles.append(
                    self.server.scene.add_box(
                        name=f"{t.id}/grid/base_x_{ix}",
                        position=(truckX + ix, l / 2, 0.0),
                        dimensions=(line_t, l, line_t),
                        color=frame_color if is_edge else grid_color,
                    )
                )
            for iy in range(l + 1):
                is_edge = iy in (0, l)
                self.truckHandles.append(
                    self.server.scene.add_box(
                        name=f"{t.id}/grid/base_y_{iy}",
                        position=(truckX + w / 2, iy, 0.0),
                        dimensions=(w, line_t, line_t),
                        color=frame_color if is_edge else grid_color,
                    )
                )

            # 2. Grid Dinding Kiri (x = 0) & Kanan (x = w) (Bidang YZ)
            for side_name, x_pos in (("left", truckX), ("right", truckX + w)):
                for iy in range(l + 1):
                    is_edge = iy in (0, l)
                    self.truckHandles.append(
                        self.server.scene.add_box(
                            name=f"{t.id}/grid/{side_name}_y_{iy}",
                            position=(x_pos, iy, h / 2),
                            dimensions=(line_t, line_t, h),
                            color=frame_color if is_edge else grid_color,
                        )
                    )
                for iz in range(1, h + 1):
                    is_edge = iz == h
                    self.truckHandles.append(
                        self.server.scene.add_box(
                            name=f"{t.id}/grid/{side_name}_z_{iz}",
                            position=(x_pos, l / 2, iz),
                            dimensions=(line_t, l, line_t),
                            color=frame_color if is_edge else grid_color,
                        )
                    )

            # 3. Grid Dinding Belakang (y = l) (Bidang XZ)
            for ix in range(1, w):
                self.truckHandles.append(
                    self.server.scene.add_box(
                        name=f"{t.id}/grid/back_x_{ix}",
                        position=(truckX + ix, l, h / 2),
                        dimensions=(line_t, line_t, h),
                        color=grid_color,
                    )
                )
            for iz in range(1, h + 1):
                is_edge = iz == h
                self.truckHandles.append(
                    self.server.scene.add_box(
                        name=f"{t.id}/grid/back_z_{iz}",
                        position=(truckX + w / 2, l, iz),
                        dimensions=(w, line_t, line_t),
                        color=frame_color if is_edge else grid_color,
                    )
                )

            def get_step(size: int) -> int:
                if size <= 10:
                    return 1
                elif size <= 50:
                    return 5
                return 10

            step_x = get_step(w)
            step_y = get_step(l)
            step_z = get_step(h)

            # 4. Angka Koordinat sesuai skala (1..10, 5..50, atau 10..100)
            for ix in range(step_x, w + 1, step_x):
                self.truckHandles.append(
                    self.server.scene.add_label(
                        name=f"{t.id}/label/x_{ix}",
                        text=str(ix),
                        position=(truckX + ix - 0.5, -0.35, 0.0),
                    )
                )
            for iy in range(step_y, l + 1, step_y):
                self.truckHandles.append(
                    self.server.scene.add_label(
                        name=f"{t.id}/label/y_{iy}",
                        text=str(iy),
                        position=(truckX - 0.35, iy - 0.5, 0.0),
                    )
                )
            for iz in range(step_z, h + 1, step_z):
                self.truckHandles.append(
                    self.server.scene.add_label(
                        name=f"{t.id}/label/z_{iz}",
                        text=str(iz),
                        position=(truckX - 0.35, 0.0, iz - 0.5),
                    )
                )

            truckX += w + gap

    def _render_packages(self, state: State):
        package_states = {
            package_state.package_id: package_state
            for package_state in state.package_states
        }

        gap = 4
        unpacked = [
            p
            for p in self.problem.packages
            if package_states.get(p.id) is None
            or package_states[p.id].placement is None
        ]
        total_width = sum(
            p.oriented_dimensions(package_states[p.id].orientation)[0]
            for p in unpacked
        )
        total_width += gap * max(len(unpacked) - 1, 0)
        cursor_x = -total_width / 2
        for package in unpacked:
            dims = package.oriented_dimensions(
                package_states[package.id].orientation
            )
            center = (cursor_x + dims[0] / 2, -gap - dims[1] / 2, dims[2] / 2)
            color = self.packageColors.get(package.id, (230, 126, 34))
            self.packageHandles[package.id] = self.server.scene.add_box(
                name=f"packages/{package.id}",
                position=center,
                dimensions=dims,
                color=color,
            )
            cursor_x += dims[0] + gap

        for package in self.problem.packages:
            package_state = package_states.get(package.id)
            placement = (
                package_state.placement if package_state is not None else None
            )
            if placement is None:
                continue
            truck = next(
                (t for t in self.problem.trucks if t.id == placement.truck_id),
                None,
            )
            if truck is None or truck.id not in self.truckOrigins:
                continue
            dims = package.oriented_dimensions(package_state.orientation)
            origin_x, origin_y = self.truckOrigins[truck.id]
            x, y, z = placement.position
            color = self.packageColors.get(package.id, (46, 204, 113))
            handle = self.server.scene.add_box(
                name=f"packages/{package.id}",
                position=(
                    origin_x + x + dims[0] / 2,
                    origin_y + y + dims[1] / 2,
                    z + dims[2] / 2,
                ),
                dimensions=dims,
                color=color,
            )
            self.packageHandles[package.id] = handle

    def _move_packages(self, state: State):
        package_states = {
            package_state.package_id: package_state
            for package_state in state.package_states
        }

        gap = 4
        unpacked = [
            p
            for p in self.problem.packages
            if package_states.get(p.id) is None
            or package_states[p.id].placement is None
        ]
        total_width = sum(
            p.oriented_dimensions(package_states[p.id].orientation)[0]
            for p in unpacked
        )
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
                handle.position = (
                    cursor_x + dims[0] / 2,
                    -gap - dims[1] / 2,
                    dims[2] / 2,
                )
                cursor_x += dims[0] + gap
            elif placement.truck_id in self.truckOrigins:
                x, y, z = placement.position
                origin_x, origin_y = self.truckOrigins[placement.truck_id]
                handle.position = (
                    origin_x + x + dims[0] / 2,
                    origin_y + y + dims[1] / 2,
                    z + dims[2] / 2,
                )

    def render(self, problem: Problem, state_or_result: State | Result):
        state = (
            state_or_result.final_state
            if isinstance(state_or_result, Result)
            else state_or_result
        )
        if self.problem != problem:
            self._cleanup()
            self.problem = problem
            self._generate_package_colors()
            self._render_trucks()
            self._render_packages(state)
        else:
            self._move_packages(state)