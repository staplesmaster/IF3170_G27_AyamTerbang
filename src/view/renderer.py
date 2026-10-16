import viser
from ..models.solution import State
from ..models.problem import Problem

class Renderer:
    server: viser.ViserServer
    problem: Problem

    truckHandles = list[viser.BoxHandle]
    packageHandles = dict[str, viser.BoxHandle]

    def __init__(self, server: viser.ViserServer):
        self.server = server
        self.truckHandles = []
        self.packageHandles = {}

    def _cleanup(self):
        for h in self.truckHandles:
            h.remove()
            self.truckHandles.clear()
            for h in self.packageHandles.values():
                h.remove()
            self.packageHandles.clear()

    def _render_trucks(self, problem: Problem):
        gap = 2.0
        wallThickness = 0.2
        totalWidth = sum(t.dimensions["w"] for t in problem.trucks)
        totalWidth += gap * max(len(problem.trucks) - 1, 0)
        truckX = -totalWidth / 2

        for t in problem.trucks:
            width = t.dimensions["w"]
            truckLength = t.dimensions["l"]
            truckHeight = t.dimensions["h"]
            centerX = truckX + width / 2
            centerY = truckLength / 2
            wallCenterZ = truckHeight / 2 + wallThickness
            self.truckHandles.extend((
                self.server.scene.add_box(
                    name=f"{t.id}/base",
                    position=(centerX, centerY, wallThickness / 2),
                    dimensions=(width, truckLength, wallThickness),
                ),
                self.server.scene.add_box(
                    name=f"{t.id}/left",
                    position=(centerX - width / 2, centerY, wallCenterZ),
                    dimensions=(wallThickness, truckLength, truckHeight),
                ),
                self.server.scene.add_box(
                    name=f"{t.id}/right",
                    position=(centerX + width / 2, centerY, wallCenterZ),
                    dimensions=(wallThickness, truckLength, truckHeight),
                ),
                self.server.scene.add_box(
                    name=f"{t.id}/front",
                    position=(centerX, centerY + truckLength / 2, wallCenterZ),
                    dimensions=(width, wallThickness, truckHeight),
                ),
            ))
            truckX += width + gap

    def _render_packages(self, state: State):
        pass

    def _move_packages(self, state: State):
        pass

    def render(self, problem: Problem, state: State):
        if self.problem != problem:
            self._cleanup()
            self.problem = problem
            self._render_trucks(problem)
            self._render_packages(state)
        else:
            self._move_packages(state)

        
        
        