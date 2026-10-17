import viser
from ..repository.parser import Parser
from .renderer import Renderer
from ..algorithm.base import Algorithm, AlgorithmOption
from ..models.problem import Problem
from ..models.solution import State

class Control:

    server: viser.ViserServer
    parser: Parser
    renderer: Renderer
    algorithms: list[Algorithm]
    selected_algorithm: int
    problem: Problem | None
    option_handles: dict[str, object]

    uploadButton: viser.GuiUploadButtonHandle
    algorithmDropdown : viser.GuiDropdownHandle
    solveButton: viser.GuiButtonHandle

    def __init__(self, server: viser.ViserServer, parser: Parser, algorithms: list[Algorithm]):
        self.server = server
        self.parser = parser
        self.algorithms = algorithms
        self.renderer = Renderer(server)
        self.selected_algorithm = 0
        self.problem = None
        self.option_handles = {}

        self.uploadButton = self.server.gui.add_upload_button("Load config", hint="Upload file konfigurasi (JSON)")

        @self.uploadButton.on_upload
        def _(event: viser.GuiEvent) -> None:
            file = event.target.value
            # parse
            try:
                problem = self.parser.parse(file)
                self.problem = problem
                initial_state = State.from_problem(problem)
                self.renderer.render(problem, initial_state)
            except RuntimeError:
                # nanti ganti error handlingnya
                print("error parsing file")

        self.algorithm_dropdown = server.gui.add_dropdown(
            "Algoritma Local Search",
            (algorithm.getName() for algorithm in self.algorithms)
        )

        self.solveButton = server.gui.add_button("Solve")

        @self.solveButton.on_click
        def _(_: viser.GuiEvent) -> None:
            if self.problem is None or not self.algorithms:
                return

            algorithm = self.algorithms[self.selected_algorithm]
            options = {key: handle.value for key, handle in self.option_handles.items()}
            state = algorithm.solve(self.problem, options=options)
            self.renderer.render(self.problem, state)

        @self.algorithm_dropdown.on_update
        def _(event: viser.GuiEvent) -> None:
            selected_name = event.target.value
            for i, algorithm in enumerate(self.algorithms):
                if algorithm.getName() == selected_name:
                    self.selected_algorithm = i
                    self._show_algorithm_options(algorithm.get_options())
                    break

        if self.algorithms:
            self._show_algorithm_options(self.algorithms[0].get_options())

    def _show_algorithm_options(self, options: list[AlgorithmOption]) -> None:
        for handle in self.option_handles.values():
            handle.remove()
        self.option_handles.clear()

        for option in options:
            if option.kind == "number":
                handle = self.server.gui.add_number(
                    option.label,
                    initial_value=option.default,
                    min=option.minimum,
                    max=option.maximum,
                    step=option.step or 0.1,
                )
            elif option.kind == "slider":
                if option.minimum is None or option.maximum is None:
                    raise ValueError(f"Slider option '{option.key}' requires minimum and maximum")
                handle = self.server.gui.add_slider(
                    option.label,
                    min=option.minimum,
                    max=option.maximum,
                    step=option.step or 0.1,
                    initial_value=option.default,
                )
            elif option.kind == "checkbox":
                handle = self.server.gui.add_checkbox(
                    option.label,
                    initial_value=option.default,
                )
            else:
                raise ValueError(f"Unsupported option type: {option.kind}")

            self.option_handles[option.key] = handle


    
