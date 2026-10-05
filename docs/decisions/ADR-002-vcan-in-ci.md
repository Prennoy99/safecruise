# ADR-002 — Virtual CAN in CI (Spike 2)

- **Status:** proposed — outcome pending the first CI run
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
without blocking the pipeline.

**CI evidence:** ⟨to be added from the first CI run: runner kernel version, outcome of both
steps, link to the `sil-vecu` job⟩

**Local evidence:** not run. It needs `sudo modprobe vcan` on the host (pb), after which
`docker run --rm --network=host -v "$PWD":/work safecruise-dev python tools/spikes/vcan_roundtrip.py vcan0`
repeats the round trip. Optional; the CI result decides.

## Consequences

- Option 1: `sil-vecu` runs its steps with `docker run --network=host` instead of a job
  `container:`, because job containers get their own network. Runner kernel updates can
  remove `vcan` from the base modules at any time; the install fallback covers that.
- Option 2: the `udp` CanIf backend is needed by M6 rather than only as a fallback, and
  the README states that CI does not exercise SocketCAN.
- Either way the spike steps in `sil-vecu` are replaced by the real SIL-vECU job in M6.
