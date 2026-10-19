from dataclasses import replace
from random import Random
from time import perf_counter

from .base import Algorithm, AlgorithmOption
from .initial_state_factory import InitialStateFactory
from .local_neighbor import RandomNeighbor
from ..models.objective import Objective
from ..models.problem import Problem
from ..models.result import Result
from ..models.solution import State


class GeneticAlgorithm(Algorithm):
    # Default fallback buat parameter
    DEFAULT_POPULATION_SIZE = 50
    DEFAULT_ITERATIONS = 200
    DEFAULT_CROSSOVER_RATE = 1  #berdasarkan ppt genetic algorithm
    DEFAULT_MUTATION_RATE = 0.2  

    def __init__(self, objective: Objective):
        self.objective = objective
        self.last_result: Result | None = None

    def getName(self) -> str:
        return "Genetic Algorithm"

    def get_options(self) -> list[AlgorithmOption]:
        return [
            AlgorithmOption("population_size", "Population size", "number", self.DEFAULT_POPULATION_SIZE,
                            minimum=2, step=1),
            AlgorithmOption("iterations", "Iterations (generations)", "number", self.DEFAULT_ITERATIONS,
                            minimum=1, step=1),
            AlgorithmOption("crossover_rate", "Crossover rate", "slider", self.DEFAULT_CROSSOVER_RATE,
                            minimum=0.0, maximum=1.0, step=0.01),
            AlgorithmOption("mutation_rate", "Mutation rate", "slider", self.DEFAULT_MUTATION_RATE,
                            minimum=0.0, maximum=1.0, step=0.01),
        ]

    def solve(self, problem: Problem, state: State, options: dict[str, int | float]) -> State:
        return self.run(problem, state, options).final_state

    def repair_state(self, problem: Problem, state: State) -> State:
        packages = {}
        trucks = {}
        for package in problem.packages:
            packages[package.id] = package
        for truck in problem.trucks:
            trucks[truck.id] = truck
        package_states = list(state.package_states)

        placed = []
        for index, package_state in enumerate(package_states):
            if package_state.placement is not None:
                z = package_state.placement.position[2]
                placed.append((z, index))
        placed.sort()

        accepted = {}
        weights = {}
        for truck in problem.trucks:
            accepted[truck.id] = []
            weights[truck.id] = 0

        for z, index in placed:
            package_state = package_states[index]
            placement = package_state.placement
            package = packages[package_state.package_id]
            truck = trucks[placement.truck_id]
            x, y, z = placement.position
            w, l, h = package.oriented_dimensions(package_state.orientation)

            valid = True
            supported = z == 0

            if x < 0 or y < 0 or z < 0:
                valid = False
            elif x + w > truck.dimensions["w"]:
                valid = False
            elif y + l > truck.dimensions["l"]:
                valid = False
            elif z + h > truck.dimensions["h"]:
                valid = False
            elif weights[truck.id] + package.weight > truck.max_capacity:
                valid = False

            if valid:
                for other_state in accepted[truck.id]:
                    other = packages[other_state.package_id]
                    ox, oy, oz = other_state.placement.position
                    ow, ol, oh = other.oriented_dimensions(other_state.orientation)
                    overlap_x = min(x + w, ox + ow) - max(x, ox)
                    overlap_y = min(y + l, oy + ol) - max(y, oy)
                    overlap_z = min(z + h, oz + oh) - max(z, oz)

                    if overlap_x > 0 and overlap_y > 0:
                        if overlap_z > 0:
                            valid = False
                            break
                        if oz + oh == z:
                            if other.is_fragile:
                                valid = False
                                break
                            supported = True

            if valid and supported:
                accepted[truck.id].append(package_state)
                weights[truck.id] += package.weight
            else:
                package_states[index] = replace(package_state, placement=None)

        return State(tuple(package_states))

    def evaluate_population(self, problem: Problem, population: list[State]) -> list[float]:
        scores = []
        for individual in population:
            scores.append(self.objective.value(problem, individual))
        return scores

    def select_parents(self, population: list[State], scores: list[float], rng: Random) -> list[State]:
        if sum(scores) == 0:
            return rng.choices(population, k=2)
        return rng.choices(population, weights=scores, k=2)

    def crossover(self, a: State, b: State, rng: Random, crossover_rate: float) -> State:
        if len(a.package_states) < 2:
            return a
        if rng.random() >= crossover_rate:
            return a
        cut = rng.randint(1, len(a.package_states) - 1)
        package_states = a.package_states[:cut] + b.package_states[cut:]
        return State(package_states)

    def run(
        self, problem: Problem, state: State, options: dict[str, int | float], *, seed: int | None = None
    ) -> Result:
        self.last_result = None
        size = int(options.get("population_size", self.DEFAULT_POPULATION_SIZE))
        iterations = int(options.get("iterations", self.DEFAULT_ITERATIONS))
        crossover_rate = float(options.get("crossover_rate", self.DEFAULT_CROSSOVER_RATE))
        mutation_rate = float(options.get("mutation_rate", self.DEFAULT_MUTATION_RATE))

        if size < 2:
            raise ValueError("Population size must be at least 2")
        if iterations < 1:
            raise ValueError("Iterations must be at least 1")
        if not 0 <= crossover_rate <= 1 or not 0 <= mutation_rate <= 1:
            raise ValueError("Crossover and mutation rates must be between 0 and 1")

        initial_state = self.repair_state(problem, state)

        rng = Random(seed)
        factory = InitialStateFactory()
        neighborhood = RandomNeighbor()

        started = perf_counter()
        population = [initial_state]
        for _ in range(size - 1):
            individual = factory.create(problem)
            population.append(self.repair_state(problem, individual))
        objective_history = []
        mean_objective_history = []

        for generation in range(iterations + 1):
            scores = self.evaluate_population(problem, population)
            best_index = scores.index(max(scores))
            objective_history.append(scores[best_index])
            mean_objective_history.append(sum(scores) / size)
            if generation == iterations:
                break

            children = [population[best_index]]
            while len(children) < size:
                parent_a, parent_b = self.select_parents(population, scores, rng)
                child = self.crossover(parent_a, parent_b, rng, crossover_rate)
                if rng.random() < mutation_rate:
                    move = next(iter(neighborhood.moves(problem, child)), None)
                    if move is not None:
                        child = move.apply(child)
                children.append(self.repair_state(problem, child))
            population = children

        final_state = population[best_index]
        result = Result(
            initial_state=initial_state,
            final_state=final_state,
            objective_value=scores[best_index],
            objective_history=tuple(objective_history),
            mean_objective_history=tuple(mean_objective_history),
            iterations=iterations,
            duration=perf_counter() - started,
        )
        self.last_result = result
        return result
