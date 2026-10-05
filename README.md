# SafeCruise

> **In progress — design and intent only, no results.**
> Nothing in this repository is a verified result yet. Numbers will appear here only once
> they come from generated artefacts of actual runs.

An Adaptive Cruise Control (ACC) feature taken through the automotive V-model: the
ISO 26262 concept phase, EARS requirements with enforced traceability, a SysML v2
architecture, AUTOSAR-Classic-style C99 software and a MIL → SIL → HIL-lite test chain.

ISO 26262 and Automotive SPICE work products are **applied concepts**, used as learning
practice. This project is not compliant, certified or assessed.

## Status

Progress by milestone is tracked in [PLAN.md](PLAN.md). Design decisions are recorded in
[docs/decisions/](docs/decisions/).

## Non-goals

Each of these rules out a claim that could otherwise be assumed.

1. **No certification, no assessment.** No confirmation review, audit or assessment has
   taken place.
2. **No real vehicle, no real sensor.** Radar, powertrain and brakes are simulated.
3. **No AUTOSAR toolchain.** No commercial AUTOSAR tools, RTE generator or ARXML authoring
   tool. The architecture is AUTOSAR-Classic-*style*.
4. **No commercial tools.** No Simulink, DOORS, Polarion, Cameo, Enterprise Architect or
   CANoe. Free equivalents are used instead.
5. **Limited feature scope.** No stop & go (minimum active speed 30 km/h), no lateral
   control, straight roads only, no reaction to stationary objects, no AEB, no camera
   fusion. Like classic ACC, it does not react to stationary objects it has not tracked as
   moving; this is a known limitation.
6. **No string stability or platooning.** A single ego vehicle.
7. **No RTOS.** A simple cyclic scheduler on host and microcontroller.
8. **No hard real-time claims.** SIL runs in lockstep simulated time. HIL-lite, if built,
   runs in soft real time on a PC and its measured jitter is published.
9. **No reproduced standard text.** Standards are referred to by name and clause only. All
   numeric values are project assumptions (`A-xx`).

## Toolchain

Everything builds and runs inside one pinned Docker image ([Dockerfile](Dockerfile)),
which also backs the [devcontainer](.devcontainer/devcontainer.json) and every CI job.

```sh
docker build --network=host -t safecruise-dev .
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/work safecruise-dev sh -c '
  cmake --preset gcc14 && cmake --build --preset gcc14 && ctest --preset gcc14 &&
  pytest &&
  sphinx-build -b html -W docs build/docs/html &&
  sphinx-build -b needs -W docs build/docs/needs'
```

The second command builds the C code and runs every test: Unity unit tests through CTest,
then pytest (tooling and requirements-database checks, SysML v2 parsing), then the docs and
the requirements export (`build/docs/needs/needs.json`). CI runs the same steps in the same
image ([.github/workflows/ci.yml](.github/workflows/ci.yml)).

## Repository layout

| Path | Contents |
|---|---|
| `docs/` | Sphinx + sphinx-needs requirements database and work products |
| `docs/decisions/` | Architecture decision records (ADRs) |
| `model/sysml/` | SysML v2 textual model |
| `swc/` | Software components: `Hmi`, `TgtSel`, `AccCtrl`, `AccMon` |
| `rte/`, `bsw/`, `platform/` | RTE configuration, basic software, platform layers |
| `can/` | CAN matrix (DBC) |
| `sim/` | Plant, traffic, sensors, MIL controller, fault injection, scenarios, KPIs |
| `tests/` | Unit (C), MIL, SIL, back-to-back and HIL tests |
| `tools/` | Project tooling (RTE generator, linters, trace gate) |

## License

[MIT](LICENSE)
