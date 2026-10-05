# ADR-002 — Virtual CAN in CI (Spike 2)

- **Status:** proposed — outcome recorded (option 1); awaiting pb's acceptance
- **Date:** 2026-10-05
- **Decided by:** pb (pending)
- **Relates to:** brief §12 M0 (Spike 2), §7.4 (SIL-vECU), [ADR-000](ADR-000-project-setup.md) D-02, D-07, D-20

## Context

The SIL-vECU level (M6) runs the full C build as a separate process that talks to the
Python harness over SocketCAN `vcan0`. CI runs every job inside the toolchain container.
Two things were unknown:

1. whether the GitHub-hosted `ubuntu-24.04` runner can load the `vcan` kernel module, and
2. whether a container started with `--network=host` can use the runner's `vcan0`.

SocketCAN interfaces belong to a network namespace, so the container must share the
host's namespace to see `vcan0`.

## Options

1. **vcan on the runner, container with `--network=host`.** Load `vcan` on the runner
   (installing `linux-modules-extra-$(uname -r)` if the module is not in the base kernel
   package), create `vcan0`, and run the vECU and harness in the container on the host
   network.
2. **UDP CanIf backend in CI.** The `udp` backend behind the same CanIf interface
   (ADR-000 D-07) carries CAN frames over loopback UDP. Works in any container, but CI
   would then not exercise the SocketCAN path.

## Decision rule (set before the run)

- Both Spike 2 steps in the `sil-vecu` job succeed → **option 1** for CI.
- Loading `vcan` fails, or the round trip from the container fails → **option 2** for CI,
  SocketCAN is exercised only locally, and the README says so.

## Evidence

Spike 2 runs in the `sil-vecu` job of `.github/workflows/ci.yml`:

- step "load vcan on the runner": `modprobe vcan` (falling back to installing
  `linux-modules-extra-$(uname -r)`), then `ip link add dev vcan0 type vcan`;
- step "CAN round trip from the container": `tools/spikes/vcan_roundtrip.py` sends one
  standard frame on `vcan0` from inside the toolchain container and expects to receive it
  unchanged within 1 s.

Both steps are `continue-on-error` so the spike records its outcome in the job summary
without blocking the pipeline. The job conclusion is therefore not the evidence; the
recorded step outcomes are.

**CI evidence:** [run #1](https://github.com/Prennoy99/safecruise/actions/runs/37376630395), commit `743bb87`, job
[`sil-vecu`](https://github.com/Prennoy99/safecruise/actions/runs/37376630395/job/111988530325), job summary "Spike 2 (ADR-002)":

| Item | Result |
|---|---|
| Runner kernel | `6.17.0-1022-azure` (`ubuntu-24.04` runner) |
| vcan on runner (step outcome) | success |
| Round trip from container, `--network=host` (step outcome) | success |

The job raised no error annotations, which agrees with both outcomes. Not recorded: whether
`modprobe vcan` worked directly or needed the `linux-modules-extra` fallback. The step log
shows it; it does not change the decision.

**Local evidence:** not run. It needs `sudo modprobe vcan` on the host (pb), after which
`docker run --rm --network=host -v "$PWD":/work safecruise-dev python tools/spikes/vcan_roundtrip.py vcan0`
repeats the round trip. Optional; the CI result decides.

## Outcome

Both conditions of the decision rule hold, so **option 1** applies: CI uses `vcan0` on the
runner with the container on the host network. The `udp` CanIf backend stays a local
fallback and the interface that keeps it possible (ADR-000 D-07) stays.

## Consequences

- Option 1: `sil-vecu` runs its steps with `docker run --network=host` instead of a job
  `container:`, because job containers get their own network. Runner kernel updates can
  remove `vcan` from the base modules at any time; the install fallback covers that.
- Option 2: the `udp` CanIf backend is needed by M6 rather than only as a fallback, and
  the README states that CI does not exercise SocketCAN.
- Either way the spike steps in `sil-vecu` are replaced by the real SIL-vECU job in M6.
