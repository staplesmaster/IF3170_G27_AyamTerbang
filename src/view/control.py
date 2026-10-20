from time import perf_counter

import numpy as np
import viser
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from ..repository.parser import Parser
from .renderer import Renderer
from ..algorithm.base import Algorithm, AlgorithmOption
from ..algorithm.genetic_algorithm import GeneticAlgorithm
from ..models.problem import Problem
from ..models.solution import State
from ..algorithm.initial_state_factory import InitialStateFactory

class Control:

    server: viser.ViserServer
    parser: Parser
    renderer: Renderer
    algorithms: list[Algorithm]
    selected_algorithm: int
    problem: Problem | None
    state: State | None
    initial_state: State | None
    option_handles: dict[str, object]

    uploadButton: viser.GuiUploadButtonHandle
    algorithm_dropdown: viser.GuiDropdownHandle
    solveButton: viser.GuiButtonHandle
    initialStateFactory: InitialStateFactory

    def __init__(self, server: viser.ViserServer, parser: Parser, algorithms: list[Algorithm]):
        self.server = server
        self.parser = parser
        self.algorithms = algorithms
        self.renderer = Renderer(server)
        self.selected_algorithm = 0
        self.problem = None
        self.state = None
        self.initial_state = None
        self.config_name = ""
        self.experiments = []
        self.running = False
        self.option_handles = {}
        self.initialStateFactory = InitialStateFactory()

        self.uploadButton = self.server.gui.add_upload_button("Load config", hint="Upload file konfigurasi (JSON)")
        self.config_text = self.server.gui.add_markdown("Belum ada konfigurasi yang dimuat.")
        self.algorithm_dropdown = server.gui.add_dropdown(
            "Algoritma Local Search",
            tuple(algorithm.getName() for algorithm in self.algorithms)
        )
        self.options_folder = self.server.gui.add_folder("Parameter algoritma")
        if self.algorithms:
            self._show_algorithm_options(self.algorithms[0].get_options())

        self.solveButton = server.gui.add_button("Solve", disabled=True)
        self.status_text = server.gui.add_markdown("", visible=False)

        with server.gui.add_folder("Hasil percobaan"):
            self.experiment_dropdown = server.gui.add_dropdown(
                "Percobaan", ("Konfigurasi aktif",), disabled=True
            )
            self.state_dropdown = server.gui.add_dropdown(
                "Tampilan state", ("State awal", "State akhir"), disabled=True
            )
            self.result_text = server.gui.add_markdown("Jalankan pencarian untuk melihat hasil.")
            self.state_text = server.gui.add_markdown("")
            self.history_image = server.gui.add_image(
                np.zeros((1, 1, 3), dtype=np.uint8),
                label="Objective per generasi", format="png", visible=False
            )

        with server.gui.add_folder("Rekap percobaan"):
            self.experiment_table = server.gui.add_markdown("Belum ada percobaan.")
            server.gui.add_markdown("Rekap disimpan selama aplikasi berjalan.")

        @self.uploadButton.on_upload
        def _(event: viser.GuiEvent) -> None:
            if self.running:
                return
            file = event.target.value
            try:
                problem = self.parser.parse(file)
                initial_state = self.initialStateFactory.create(problem)
            except (RuntimeError, ValueError, KeyError, TypeError):
                self.status_text.content = "Konfigurasi gagal dimuat. Periksa isi file JSON."
                self.status_text.visible = True
                return

            self.problem = problem
            self.initial_state = initial_state
            self.state = initial_state
            self.config_name = file.name
            self.config_text.content = (
                f"**Konfigurasi aktif:** {self.config_name}\n\n"
                f"Paket: {len(problem.packages)} · Truk: {len(problem.trucks)}\n\n"
                "Solve memakai konfigurasi ini dan state awal yang sama pada setiap percobaan."
            )
            self.experiment_dropdown.value = "Konfigurasi aktif"
            self._show_experiment()
            self.status_text.visible = False
            self.solveButton.disabled = not self.algorithms

        @self.solveButton.on_click
        def _(_: viser.GuiEvent) -> None:
            if self.running or self.problem is None or self.initial_state is None or not self.algorithms:
                return

            algorithm = self.algorithms[self.selected_algorithm]
            options = {key: handle.value for key, handle in self.option_handles.items()}
            self._set_running(True)
            self.status_text.content = "Pencarian sedang berjalan..."
            self.status_text.visible = True
            try:
                started = perf_counter()
                final_state = algorithm.solve(self.problem, self.initial_state, options=options)
                duration = perf_counter() - started
                initial_state = self.initial_state
                result = None

                if isinstance(algorithm, GeneticAlgorithm):
                    result = algorithm.last_result
                    initial_state = result.initial_state
                    duration = result.duration
                    objective = result.objective_value
                else:
                    objective = algorithm.objective.value(self.problem, final_state)

                self.state = final_state
                self.experiments.append({
                    "problem": self.problem,
                    "config": self.config_name,
                    "algorithm": algorithm.getName(),
                    "options": options,
                    "initial_state": initial_state,
                    "final_state": final_state,
                    "initial_objective": algorithm.objective.value(self.problem, initial_state),
                    "objective": objective,
                    "duration": duration,
                    "result": result,
                })
                choices = ["Konfigurasi aktif"]
                for index in range(len(self.experiments)):
                    choices.append(f"Percobaan {index + 1}")
                self.experiment_dropdown.options = tuple(choices)
                self._update_experiment_table()
             
                self.experiment_dropdown.value = choices[-1]
                self.status_text.content = "Pencarian selesai. Ubah parameter untuk percobaan berikutnya."
            except (ValueError, RuntimeError) as error:
                self.status_text.content = f"Pencarian gagal: {error}"
            finally:
                self._set_running(False)

        @self.algorithm_dropdown.on_update
        def _(event: viser.GuiEvent) -> None:
            selected_name = event.target.value
            for i, algorithm in enumerate(self.algorithms):
                if algorithm.getName() == selected_name:
                    self.selected_algorithm = i
                    self._show_algorithm_options(algorithm.get_options())
                    break

        @self.experiment_dropdown.on_update
        def _(_: viser.GuiEvent) -> None:
            self._show_experiment()

        @self.state_dropdown.on_update
        def _(_: viser.GuiEvent) -> None:
            self._render_selected_state()

    def _set_running(self, running: bool) -> None:
        self.running = running
        self.solveButton.disabled = running or self.problem is None or not self.algorithms
        self.uploadButton.disabled = running
        self.algorithm_dropdown.disabled = running
        for handle in self.option_handles.values():
            handle.disabled = running
        self.experiment_dropdown.disabled = running or not self.experiments
        self.state_dropdown.disabled = running or self.experiment_dropdown.value == "Konfigurasi aktif"

    def _show_experiment(self) -> None:
        if self.experiment_dropdown.value == "Konfigurasi aktif":
            self.state_dropdown.value = "State awal"
            self.state_dropdown.disabled = True
            self.result_text.content = "Jalankan pencarian untuk melihat hasil konfigurasi aktif."
            self.history_image.visible = False
            self._render_selected_state()
            return

        index = self.experiment_dropdown.options.index(self.experiment_dropdown.value) - 1
        experiment = self.experiments[index]
        result = experiment["result"]
        population = "—"
        iterations = "Belum dicatat"
        if result is not None:
            population = int(experiment["options"]["population_size"])
            iterations = result.iterations

        self.result_text.content = (
            f"**Percobaan {index + 1}: {experiment['algorithm']}**\n\n"
            f"Konfigurasi: {experiment['config']}\n\n"
            "| Pengukuran | Hasil |\n|---|---:|\n"
            f"| Objective awal | {experiment['initial_objective']:.2f} |\n"
            f"| Objective akhir | {experiment['objective']:.2f} |\n"
            f"| Jumlah populasi | {population} |\n"
            f"| Banyak iterasi | {iterations} |\n"
            f"| Durasi pencarian | {experiment['duration']:.4f} detik |"
        )
        if result is not None:
            self.result_text.content += (
                f"\n| Crossover rate | {experiment['options']['crossover_rate']:.2f} |"
                f"\n| Mutation rate | {experiment['options']['mutation_rate']:.2f} |"
            )
            self._show_history(result.objective_history, result.mean_objective_history)
        else:
            self.result_text.content += "\n\nRiwayat pencarian belum tersedia untuk algoritma ini."
            self.history_image.visible = False

        self.state_dropdown.disabled = False
        self.state_dropdown.value = "State akhir"
        self._render_selected_state()

    def _render_selected_state(self) -> None:
        if self.experiment_dropdown.value == "Konfigurasi aktif":
            problem = self.problem
            state = self.initial_state
        else:
            index = self.experiment_dropdown.options.index(self.experiment_dropdown.value) - 1
            experiment = self.experiments[index]
            problem = experiment["problem"]
            if self.state_dropdown.value == "State awal":
                state = experiment["initial_state"]
            else:
                state = experiment["final_state"]

        if problem is None or state is None:
            return
        self.renderer.render(problem, state)
        self.state_text.content = (
            f"**{self.state_dropdown.value}** · Paket dimuat: "
            f"{len(state.placed_package_ids)} / {len(problem.packages)}"
        )

    def _show_history(self, objective_history, mean_objective_history) -> None:
        generations = range(len(objective_history))

        figure = Figure(figsize=(5, 3), dpi=140)
        axis = figure.subplots()
        axis.plot(generations, objective_history, color="#386641", label="Maksimum", linewidth=2)
        axis.plot(generations, mean_objective_history, color="#386641", label="Rata-rata", linestyle="--")
        axis.set_xlabel("Generasi")
        axis.set_ylabel("Objective function")
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        axis.grid(alpha=0.25)
        axis.legend()
        figure.tight_layout()

        canvas = FigureCanvasAgg(figure)
        canvas.draw()
        self.history_image.image = np.asarray(canvas.buffer_rgba()).copy()
        self.history_image.visible = True

    def _update_experiment_table(self) -> None:
        rows = [
            "| Run | Konfigurasi | Algoritma | Populasi | Iterasi | Cross. | Mut. | Objective | Detik |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for index, experiment in enumerate(self.experiments):
            result = experiment["result"]
            population = "—"
            iterations = "—"
            crossover = "—"
            mutation = "—"
            if result is not None:
                population = int(experiment["options"]["population_size"])
                iterations = result.iterations
                crossover = f"{experiment['options']['crossover_rate']:.2f}"
                mutation = f"{experiment['options']['mutation_rate']:.2f}"
            config = experiment["config"].replace("|", "\\|").replace("\n", " ")
            rows.append(
                f"| {index + 1} | {config} | {experiment['algorithm']} | {population} | "
                f"{iterations} | {crossover} | {mutation} | {experiment['objective']:.2f} | "
                f"{experiment['duration']:.4f} |"
            )
        self.experiment_table.content = "\n".join(rows)

    def _show_algorithm_options(self, options: list[AlgorithmOption]) -> None:
        for handle in self.option_handles.values():
            handle.remove()
        self.option_handles.clear()

        with self.options_folder:
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
